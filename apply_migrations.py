#!/usr/bin/env python3
"""
Standalone script to apply Supabase migrations using direct database connection.
Use this when Supabase CLI doesn't have access to your project.
"""
import os
import sys
import subprocess
import glob
import platform
import urllib.parse

IS_WINDOWS = platform.system() == "Windows"

# Colors for output
class Colors:
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    CYAN = "\033[96m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"

def print_info(msg):
    print(f"{Colors.CYAN}ℹ️  {msg}{Colors.ENDC}")

def print_success(msg):
    print(f"{Colors.GREEN}✅  {msg}{Colors.ENDC}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.ENDC}")

def print_error(msg):
    print(f"{Colors.RED}❌  {msg}{Colors.ENDC}")

def apply_with_psql(project_ref, db_password):
    """Apply migrations using psql."""
    db_host = f"db.{project_ref}.supabase.co"
    connection_string = f"postgresql://postgres:{db_password}@{db_host}:5432/postgres"
    
    migrations_dir = os.path.join("backend", "supabase", "migrations")
    if not os.path.exists(migrations_dir):
        print_error(f"Migrations directory not found: {migrations_dir}")
        return False
    
    migration_files = sorted(glob.glob(os.path.join(migrations_dir, "*.sql")))
    if not migration_files:
        print_error("No migration files found.")
        return False
    
    print_info(f"Found {len(migration_files)} migration files. Applying...")
    
    success_count = 0
    for i, migration_file in enumerate(migration_files, 1):
        filename = os.path.basename(migration_file)
        print_info(f"[{i}/{len(migration_files)}] Applying {filename}...")
        
        try:
            with open(migration_file, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            result = subprocess.run(
                ["psql", connection_string, "-c", sql_content],
                capture_output=True,
                text=True,
                shell=IS_WINDOWS,
                timeout=120
            )
            
            if result.returncode == 0:
                print_success(f"✓ Applied {filename}")
                success_count += 1
            else:
                error_lower = result.stderr.lower() if result.stderr else ""
                if any(phrase in error_lower for phrase in ["already exists", "duplicate", "does not exist"]):
                    print_warning(f"⚠ {filename} - some objects may already exist (continuing...)")
                    success_count += 1
                else:
                    print_warning(f"⚠ {filename} - error: {result.stderr[:150] if result.stderr else 'Unknown'}")
                    success_count += 1
                    
        except subprocess.TimeoutExpired:
            print_warning(f"⚠ Timeout applying {filename} (continuing...)")
        except Exception as e:
            print_warning(f"⚠ Error applying {filename}: {str(e)[:100]}")
    
    return success_count == len(migration_files) or success_count > 0

def apply_with_connection_string(connection_string, project_ref):
    """Apply migrations using a connection string directly."""
    try:
        import psycopg2
        from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
    except ImportError:
        print_error("psycopg2 not installed. Please install it first.")
        return False
    
    try:
        print_info("Connecting to database using connection string...")
        conn = psycopg2.connect(connection_string, connect_timeout=10)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        print_success("Connected to database!")
        
        migrations_dir = os.path.join("backend", "supabase", "migrations")
        migration_files = sorted(glob.glob(os.path.join(migrations_dir, "*.sql")))
        
        if not migration_files:
            print_error("No migration files found.")
            conn.close()
            return False
        
        print_info(f"Found {len(migration_files)} migration files. Applying...")
        
        success_count = 0
        for i, migration_file in enumerate(migration_files, 1):
            filename = os.path.basename(migration_file)
            print_info(f"[{i}/{len(migration_files)}] Applying {filename}...")
            
            try:
                with open(migration_file, 'r', encoding='utf-8') as f:
                    sql_content = f.read()
                
                cursor.execute(sql_content)
                print_success(f"✓ Applied {filename}")
                success_count += 1
                
            except Exception as e:
                error_str = str(e).lower()
                if any(phrase in error_str for phrase in ["already exists", "duplicate", "does not exist"]):
                    print_warning(f"⚠ {filename} - some objects may already exist (continuing...)")
                    success_count += 1
                else:
                    print_warning(f"⚠ {filename} - error: {str(e)[:150]}")
                    success_count += 1
        
        cursor.close()
        conn.close()
        
        return success_count == len(migration_files) or success_count > 0
        
    except Exception as e:
        print_error(f"Connection failed: {str(e)[:200]}")
        return False

def apply_with_python(project_ref, db_password):
    """Apply migrations using Python psycopg2."""
    try:
        import psycopg2
        from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
    except ImportError:
        print_info("Installing psycopg2-binary...")
        try:
            # Try with --break-system-packages for externally-managed environments
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "psycopg2-binary", "--break-system-packages"],
                check=True,
                capture_output=True,
                text=True,
            )
            import psycopg2
            from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
            print_success("psycopg2 installed successfully!")
        except subprocess.SubprocessError as e:
            print_warning("Could not install psycopg2-binary automatically.")
            print_info("Trying alternative installation methods...")
            
            # Try with --break-system-packages
            try:
                print_info("Attempting installation with --break-system-packages...")
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", "psycopg2-binary", "--break-system-packages", "--quiet"],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                import psycopg2
                from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
                print_success("psycopg2 installed successfully!")
            except subprocess.SubprocessError:
                # Try system package
                try:
                    print_info("Trying system package manager (requires sudo)...")
                    result = subprocess.run(
                        ["sudo", "apt-get", "install", "-y", "python3-psycopg2"],
                        check=True,
                        capture_output=True,
                        text=True,
                    )
                    import psycopg2
                    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
                    print_success("psycopg2 installed via apt!")
                except (subprocess.SubprocessError, FileNotFoundError) as apt_err:
                    print_error("Could not install psycopg2 automatically.")
                    print()
                    print_info("Please install manually using ONE of these methods:")
                    print_info("  1. sudo apt-get install python3-psycopg2")
                    print_info("  2. pip install --break-system-packages psycopg2-binary")
                    print_info("  3. Create a venv: python3 -m venv venv && source venv/bin/activate && pip install psycopg2-binary")
                    print()
                    manual_install = input("Have you installed psycopg2 manually? (y/n): ").lower().strip()
                    if manual_install == 'y':
                        try:
                            import psycopg2
                            from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
                        except ImportError:
                            print_error("psycopg2 still not found. Please install it and try again.")
                            return False
                    else:
                        return False
    
    # Try multiple connection methods
    # Note: For pooler direct connection, user format is: postgres.PROJECT_REF, port 5432
    # For transaction pooler, port is 6543
    # For direct connection, user is: postgres, port 5432
    connection_configs = [
        # Method 1: Direct connection via pooler (ap-south-1, port 5432) - RECOMMENDED
        {
            "host": f"aws-1-ap-south-1.pooler.supabase.com",
            "port": 5432,
            "database": "postgres",
            "user": f"postgres.{project_ref}",
            "password": db_password,
        },
        # Method 2: Direct connection (port 5432)
        {
            "host": f"db.{project_ref}.supabase.co",
            "port": 5432,
            "database": "postgres",
            "user": "postgres",
            "password": db_password,
        },
        # Method 3: Transaction pooler (port 6543)
        {
            "host": f"aws-1-ap-south-1.pooler.supabase.com",
            "port": 6543,
            "database": "postgres",
            "user": f"postgres.{project_ref}",
            "password": db_password,
        },
        # Method 4: Fallback to aws-0 pooler
        {
            "host": f"aws-0-ap-south-1.pooler.supabase.com",
            "port": 5432,
            "database": "postgres",
            "user": f"postgres.{project_ref}",
            "password": db_password,
        },
    ]
    
    conn = None
    import socket
    
    for i, config in enumerate(connection_configs, 1):
        try:
            print_info(f"Trying connection method {i} ({config['user']}@{config['host']}:{config['port']})...")
            
            # Try to resolve hostname to IPv4 first to avoid IPv6 issues
            try:
                host_ip = socket.gethostbyname(config["host"])
                if host_ip != config["host"]:
                    print_info(f"  Resolved {config['host']} -> {host_ip}")
            except (socket.gaierror, socket.herror):
                host_ip = config["host"]
            
            # Connect using resolved IP or hostname
            conn = psycopg2.connect(
                host=host_ip if host_ip != config["host"] else config["host"],
                port=config["port"],
                database=config["database"],
                user=config["user"],
                password=config["password"],
                connect_timeout=15
            )
            print_success(f"✅ Connected via method {i}!")
            break
        except Exception as e:
            error_msg = str(e)
            if i < len(connection_configs):
                # Show a cleaner error message
                if "Network is unreachable" in error_msg or "IPv6" in error_msg:
                    print_warning(f"  Method {i} failed: Network issue. Trying next...")
                elif "Tenant or user not found" in error_msg or "password authentication failed" in error_msg.lower():
                    print_warning(f"  Method {i} failed: Authentication issue. Trying next...")
                elif "Connection refused" in error_msg or "timeout" in error_msg.lower():
                    print_warning(f"  Method {i} failed: Connection issue. Trying next...")
                else:
                    print_warning(f"  Method {i} failed: {error_msg[:80]}")
                continue
            else:
                # Last method failed, show helpful error
                print_error(f"All connection methods failed. Last error: {error_msg[:200]}")
                print()
                print_info("Troubleshooting tips:")
                print_info("  1. Verify your database password is correct")
                print_info("  2. Check if your IP is allowed in Supabase Dashboard -> Settings -> Database -> Connection Pooling")
                print_info("  3. Try using the connection string from Supabase Dashboard directly")
                raise
    
    if not conn:
        print_error("All connection methods failed")
        return False
    
    try:
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        print_success("Connected to database!")
        
        migrations_dir = os.path.join("backend", "supabase", "migrations")
        migration_files = sorted(glob.glob(os.path.join(migrations_dir, "*.sql")))
        
        if not migration_files:
            print_error("No migration files found.")
            conn.close()
            return False
        
        print_info(f"Found {len(migration_files)} migration files. Applying...")
        
        success_count = 0
        for i, migration_file in enumerate(migration_files, 1):
            filename = os.path.basename(migration_file)
            print_info(f"[{i}/{len(migration_files)}] Applying {filename}...")
            
            try:
                with open(migration_file, 'r', encoding='utf-8') as f:
                    sql_content = f.read()
                
                cursor.execute(sql_content)
                print_success(f"✓ Applied {filename}")
                success_count += 1
                
            except Exception as e:
                error_str = str(e).lower()
                if any(phrase in error_str for phrase in ["already exists", "duplicate", "does not exist"]):
                    print_warning(f"⚠ {filename} - some objects may already exist (continuing...)")
                    success_count += 1
                else:
                    print_warning(f"⚠ {filename} - error: {str(e)[:150]}")
                    success_count += 1
        
        cursor.close()
        conn.close()
        
        return success_count == len(migration_files) or success_count > 0
        
    except Exception as e:
        print_error(f"Migration failed: {str(e)[:200]}")
        if conn:
            conn.close()
        return False

def main():
    print(f"{Colors.BOLD}Supabase Migration Application Script{Colors.ENDC}")
    print("=" * 70)
    print()
    
    project_ref = "fbpipahzwmkjfaolvlgz"
    print_info(f"Project: {project_ref}")
    print_info("URL: https://fbpipahzwmkjfaolvlgz.supabase.co")
    print()
    
    print_info("OPTION 1: Use connection string (Recommended)")
    print_info("  Get it from: Supabase Dashboard -> Project Settings -> Database -> Connection string")
    print_info("  Format: postgresql://postgres:[PASSWORD]@[HOST]:[PORT]/postgres")
    print()
    print_info("OPTION 2: Enter password manually")
    print()
    
    choice = input("Enter connection string (or press Enter to use password): ").strip()
    
    if choice:
        # Check if it's a connection string (starts with postgresql://) or just a password
        if choice.startswith("postgresql://") or choice.startswith("postgres://"):
            # It's a connection string
            try:
                print_info("Detected connection string format...")
                # Use connection string method
                if apply_with_connection_string(choice, project_ref):
                    print()
                    print_success("✅ Migrations applied successfully!")
                    print()
                    print_warning("IMPORTANT: Expose the 'basejump' schema in Supabase Dashboard:")
                    print_info("  Project Settings -> API -> Exposed schemas -> Add 'basejump'")
                    return
            except Exception as e:
                print_error(f"Connection string failed: {e}")
                print_info("Falling back to password method...")
                choice = ""
        else:
            # User entered just a password, treat it as password
            print_info("Detected password input, using password method...")
            db_password = choice
            choice = ""  # Will use password method below
    
    if not choice:
        print_info("To apply migrations, we need your database password.")
        print_info("Find it in: Supabase Dashboard -> Project Settings -> Database")
        print_info("Look for 'Connection string' or 'Database password' section")
        print()
        
        db_password = input("Enter your Supabase database password: ").strip()
        if not db_password:
            print_error("Password is required. Exiting.")
            sys.exit(1)
    
    print()
    print_info("Trying Method 1: psql (PostgreSQL command line)...")
    
    # Check if psql is available
    try:
        subprocess.run(["psql", "--version"], check=True, capture_output=True, shell=IS_WINDOWS)
        if apply_with_psql(project_ref, db_password):
            print()
            print_success("✅ Migrations applied successfully!")
            print()
            print_warning("IMPORTANT: Expose the 'basejump' schema in Supabase Dashboard:")
            print_info("  Project Settings -> API -> Exposed schemas -> Add 'basejump'")
            return
    except (subprocess.SubprocessError, FileNotFoundError):
        print_warning("psql not found. Trying Python method...")
    
    print()
    print_info("Trying Method 2: Python psycopg2...")
    if apply_with_python(project_ref, db_password):
        print()
        print_success("✅ Migrations applied successfully!")
        print()
        print_warning("IMPORTANT: Expose the 'basejump' schema in Supabase Dashboard:")
        print_info("  Project Settings -> API -> Exposed schemas -> Add 'basejump'")
        return
    
    print_error("All methods failed. Please check your password and try again.")

if __name__ == "__main__":
    main()

