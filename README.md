# Gateway Application - jungholm industries

A cross-platform desktop gateway application for researchers to activate lab instruments.

## Features

- **Cross-platform**: Works on macOS, Windows, and Linux
- **Secure Authentication**: Email/password login via Supabase GoTrue
- **Instrument Management**: List and select instruments from Supabase
- **Session Tracking**: Start/stop instrument sessions with automatic time tracking
- **Offline Support**: Queue events locally when offline, retry with exponential backoff
- **Secure Storage**: Tokens stored in OS keychain (macOS Keychain, Windows Credential Manager, Linux Secret Service)

## Requirements

- Python 3.8+
- Supabase project with the following tables:
  - `products` table (represents instruments/equipment) with at least `id` and `name` columns
  - `product_consumption` table for tracking instrument usage sessions
  - `profiles` table (user profiles linked to auth.users)
  - `bookings` table (for booking management, optional for consumption tracking)

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure Supabase credentials:
   - Copy `.env.example` to `.env`
   - Fill in your `SUPABASE_URL` and `SUPABASE_KEY`
   - Or set them as environment variables

## Usage

Run the application:
```bash
python main.py
```

1. Login with your Supabase credentials
2. Select an instrument from the dropdown
3. Click "Activate" to start a session
4. Click "Stop" to end the session
5. Usage data is automatically uploaded to Supabase

## Database Schema

The application uses the following Supabase tables:

### products table
Represents instruments/equipment available for use. The application fetches products with `status = 'active'`.

### product_consumption table
Tracks instrument/product consumption sessions:
- `id`: UUID primary key
- `product_id`: References products.id
- `user_id`: References profiles.id (which references auth.users.id)
- `booking_id`: References bookings.id (nullable, for testing)
- `start_time`: Timestamp when session started
- `end_time`: Timestamp when session ended (null while active)
- `duration_seconds`: Calculated duration in seconds (null while active)
- `status`: 'active', 'completed', or 'timeout'
- `created_at`, `updated_at`: Timestamps

### profiles table
User profiles linked to Supabase auth.users.

### bookings table
Booking records. The gateway app automatically creates minimal bookings for gateway sessions. Can be linked to consumption records via `booking_id` (nullable).

## Security

- Passwords are never stored locally
- Access tokens stored securely in OS keychain
- All communication with Supabase uses HTTPS
- Row Level Security (RLS) should be enabled on Supabase tables

## Offline Support

When offline, events are queued locally and automatically retried when connection is restored. The retry mechanism uses exponential backoff to avoid overwhelming the server.

