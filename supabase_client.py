"""Supabase client wrapper with session management"""
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY
from secure_storage import SecureStorage
from offline_queue import OfflineQueue

logger = logging.getLogger(__name__)


class SupabaseClient:
    """Wrapper for Supabase client with authentication and session management"""
    
    def __init__(self):
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")
        
        self.client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.storage = SecureStorage()
        self.offline_queue = OfflineQueue()
        self._restore_session()
    
    def _restore_session(self):
        """Restore session from stored tokens"""
        token = self.storage.get_token()
        refresh_token = self.storage.get_refresh_token()
        
        if token and refresh_token:
            try:
                # Set the session
                self.client.auth.set_session(token, refresh_token)
                logger.info("Session restored from storage")
            except Exception as e:
                logger.error(f"Failed to restore session: {e}")
                self.storage.clear_all()
    
    def login(self, email: str, password: str) -> Tuple[bool, Optional[str]]:
        """
        Login with email and password
        Returns: (success, error_message)
        """
        try:
            response = self.client.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if response.user:
                # Store tokens securely
                session = response.session
                if session:
                    self.storage.save_token(session.access_token)
                    self.storage.save_refresh_token(session.refresh_token)
                    self.storage.save_user_id(response.user.id)
                    logger.info(f"Login successful for user: {email}")
                    return True, None
                else:
                    return False, "No session returned"
            else:
                return False, "Invalid credentials"
        
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Login failed: {error_msg}")
            return False, error_msg
    
    def logout(self):
        """Logout and clear stored credentials"""
        try:
            self.client.auth.sign_out()
        except Exception as e:
            logger.error(f"Error during logout: {e}")
        finally:
            self.storage.clear_all()
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        try:
            user = self.client.auth.get_user()
            return user is not None
        except Exception:
            return False
    
    def get_current_user(self):
        """Get current authenticated user"""
        try:
            return self.client.auth.get_user()
        except Exception:
            return None
    
    def get_instruments(self) -> List[Dict[str, Any]]:
        """Fetch list of products (instruments) from Supabase"""
        try:
            # Only fetch active products
            response = self.client.table("products").select("*").eq("status", "active").execute()
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Failed to fetch products: {e}")
            return []
    
    def start_session(self, product_id: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Start a usage session
        Returns: (success, session_id, error_message)
        """
        try:
            user = self.get_current_user()
            if not user:
                return False, None, "Not authenticated"
            
            # Get user profile ID
            # Since profiles.id references auth.users.id, they're the same UUID
            profile_id = user.user.id
            
            # Verify profile exists
            profile_response = self.client.table("profiles").select("id").eq("id", profile_id).execute()
            if not profile_response.data or len(profile_response.data) == 0:
                return False, None, "User profile not found"
            
            # Look for an existing active confirmed booking for this user/product
            # Since booking happens elsewhere, we should use existing bookings when possible
            start_time = datetime.now(timezone.utc)
            now_iso = start_time.isoformat()
            
            # Check for existing active confirmed bookings (start_time <= now AND end_time >= now)
            existing_booking_response = self.client.table("bookings").select("*").eq(
                "user_id", profile_id
            ).eq(
                "product_id", product_id
            ).eq(
                "status", "confirmed"
            ).lte("start_time", now_iso).gte("end_time", now_iso).execute()
            
            booking_id = None
            
            if existing_booking_response.data and len(existing_booking_response.data) > 0:
                # Use existing active booking (take the first one if multiple)
                booking_id = existing_booking_response.data[0]["id"]
                logger.info(f"Using existing booking: {booking_id}")
            else:
                # Create a minimal gateway booking with status 'cancelled' to avoid constraint conflicts
                # The exclusion constraint only applies to 'confirmed' bookings
                end_time = start_time.replace(hour=23, minute=59, second=59)  # End of day as placeholder
                
                booking_data = {
                    "user_id": profile_id,
                    "product_id": product_id,
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "status": "cancelled",  # Use 'cancelled' to avoid exclusion constraint
                    "legal_agreement_accepted": True,
                    "notes": "Gateway session - automatic booking placeholder"
                }
                
                booking_response = self.client.table("bookings").insert(booking_data).execute()
                
                if not booking_response.data or len(booking_response.data) == 0:
                    return False, None, "Failed to create gateway booking"
                
                booking_id = booking_response.data[0]["id"]
                logger.info(f"Created gateway booking: {booking_id}")
            
            # Create consumption record for this session
            consumption_data = {
                "product_id": product_id,
                "user_id": profile_id,
                "booking_id": booking_id,  # Nullable, can be None for testing
                "start_time": start_time.isoformat(),
                "status": "active"
            }
            
            consumption_response = self.client.table("product_consumption").insert(consumption_data).execute()
            
            if consumption_response.data and len(consumption_response.data) > 0:
                consumption_id = consumption_response.data[0].get("id")
                logger.info(f"Consumption session started: {consumption_id}, booking: {booking_id}")
                return True, consumption_id, None
            else:
                return False, None, "Failed to create consumption record"
        
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to start session: {error_msg}")
            # Queue for offline retry
            self.offline_queue.add_event("start_session", {
                "product_id": product_id,
                "user_id": self.storage.get_user_id()
            })
            return False, None, error_msg
    
    def stop_session(self, session_id: str) -> Tuple[bool, Optional[str]]:
        """
        Stop a usage session
        Updates the product_consumption record with end_time and duration
        Returns: (success, error_message)
        """
        try:
            # Get consumption record to calculate duration
            consumption_response = self.client.table("product_consumption").select("*").eq("id", session_id).execute()
            
            if not consumption_response.data or len(consumption_response.data) == 0:
                return False, "Consumption session not found"
            
            consumption = consumption_response.data[0]
            start_time = consumption.get("start_time")
            
            if not start_time:
                return False, "Consumption session has no start time"
            
            # Calculate duration in seconds
            end_time_dt = datetime.now(timezone.utc)
            end_time = end_time_dt.isoformat()
            
            # Parse start_time from Supabase (it's timezone-aware)
            start_time_str = start_time.replace('Z', '+00:00') if 'Z' in start_time else start_time
            start_dt = datetime.fromisoformat(start_time_str)
            
            # Ensure both are timezone-aware for comparison
            if start_dt.tzinfo is None:
                start_dt = start_dt.replace(tzinfo=timezone.utc)
            
            duration_seconds = int((end_time_dt - start_dt).total_seconds())
            
            # Update consumption record
            update_data = {
                "end_time": end_time,
                "duration_seconds": duration_seconds,
                "status": "completed"
            }
            
            try:
                # Update the consumption record
                table_ref = self.client.table("product_consumption")
                update_ref = table_ref.update(update_data)
                filter_ref = update_ref.eq("id", session_id)
                response = filter_ref.execute()
                
                # Check for errors
                if hasattr(response, 'error') and response.error:
                    error_msg = str(response.error)
                    logger.error(f"Supabase update error: {error_msg}")
                    return False, f"Update failed: {error_msg}"
                
                logger.info(f"Consumption session stopped: {session_id}, duration: {duration_seconds}s")
                
                # Verify the update
                verify_response = self.client.table("product_consumption").select("id, end_time, duration_seconds").eq("id", session_id).execute()
                
                if verify_response.data and len(verify_response.data) > 0:
                    updated_consumption = verify_response.data[0]
                    if updated_consumption.get("end_time") and updated_consumption.get("end_time") != consumption.get("end_time"):
                        logger.info(f"Session stopped successfully: {session_id}, duration: {duration_seconds}s")
                        return True, None
                    else:
                        return False, "Update verification failed"
                else:
                    return False, "Could not verify update"
                    
            except Exception as update_error:
                error_msg = f"Update failed: {str(update_error)}"
                logger.error(f"Failed to update consumption: {error_msg}")
                # Queue for offline retry
                self.offline_queue.add_event("stop_session", {
                    "session_id": session_id
                })
                return False, error_msg
        
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to stop session: {error_msg}")
            # Queue for offline retry
            self.offline_queue.add_event("stop_session", {
                "session_id": session_id
            })
            return False, error_msg
    
    def process_offline_queue(self):
        """Process queued offline events"""
        def process_start_session(event):
            data = event["data"]
            # Handle both old 'instrument_id' and new 'product_id' keys for backward compatibility
            product_id = data.get("product_id") or data.get("instrument_id")
            if product_id:
                success, session_id, error = self.start_session(product_id)
                return success
            return False
        
        def process_stop_session(event):
            data = event["data"]
            success, error = self.stop_session(data["session_id"])
            return success
        
        def processor(event):
            event_type = event["type"]
            if event_type == "start_session":
                return process_start_session(event)
            elif event_type == "stop_session":
                return process_stop_session(event)
            return False
        
        return self.offline_queue.process_queue(processor)

