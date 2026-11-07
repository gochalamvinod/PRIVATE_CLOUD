import json
import os
import sys
import re
import urllib.request
from pathlib import Path

try:
    from mega import Mega
    mega = Mega()
except ImportError:
    mega = None

try:
    from crypto.encrypt import encrypt_file, decrypt_file
except ImportError:
    from .crypto.encrypt import encrypt_file, decrypt_file

def get_file_name(file_path):
    """Extracts file or folder name from the path using standard pathlib."""
    return Path(file_path).name

def password_checker(email, password):
    """Checks if the credentials are valid."""
    if not mega:
        return False
    try:
        mega.login(email, password)
        return True
    except Exception:
        return False

def login_to_mega(email, password):
    """Logs into Mega and returns the login cookie."""
    if password_checker(email, password):
        return mega.login(email, password)
    return None

def get_storage_details(login_cookie):
    """Retrieves storage details of the logged-in user."""
    if not login_cookie:
        raise ValueError("Invalid login session.")
    
    space = login_cookie.get_storage_space(kilo=True)
    total = space['total']
    used = space['used']
    remain = total - used
    
    return {'total': total, 'used': used, 'remaining': remain}

def upload_and_generate_info(login_cookie, file_path, root_path, email, password):
    """Uploads a file to Mega and generates a shareable link."""
    if not login_cookie:
        raise ValueError("Invalid login session.")
    
    uploaded_file = login_cookie.upload(file_path)
    link = login_cookie.get_upload_link(uploaded_file)
    return [email, password, root_path, link]

def file_size(filepath):
    """Returns the size of the file using standard os.path."""
    try:
        if not os.path.exists(filepath):
            raise FileNotFoundError("The specified file does not exist.")
        
        return os.path.getsize(filepath)
    
    except Exception as e:
        return f"Error: {e}"

def load_accounts_from_json(json_file):
    """Loads MEGA account credentials from a JSON file using standard json."""
    try:
        with open(json_file, 'r', encoding='utf-8') as file:
            accounts = json.load(file)
            return [(account['email'], account['password']) for account in accounts]
    except Exception as e:
        return f"Error loading JSON file: {e}"

def find_account_with_sufficient_storage(json_file, file_path):
    """Finds an account with enough storage space for the file."""
    accounts = load_accounts_from_json(json_file)
    if isinstance(accounts, str):
        return accounts
    
    file_size_in_bytes = file_size(file_path)
    if isinstance(file_size_in_bytes, str):
        return file_size_in_bytes
    
    for email, password in accounts:
        login_cookie = login_to_mega(email, password)
        if login_cookie:
            storage_details = get_storage_details(login_cookie)
            available_space = storage_details['remaining']
            if available_space >= file_size_in_bytes:
                return [email, password]
    
    return "No account has enough storage for the file upload."

def path_keeper_server(root_path, link_path, text_file):
    """Appends the root path and link to a server file."""
    try:
        with open(text_file, 'a', encoding='utf-8') as file:
            line = f"{root_path} => {link_path}\n"
            file.write(line)
        return "Path added successfully."
    except Exception as e:
        return f"Error appending path: {e}"

def path_keeper(root_path, text_file):
    """Appends the root path to a file."""
    try:
        with open(text_file, 'a', encoding='utf-8') as file:
            line = f"{root_path}\n"
            file.write(line)
        return "Path added successfully."
    except Exception as e:
        return f"Error appending path: {e}"

def upload_folder(login_cookie, folder_path, root_path, email, password):
    """Uploads a folder to MEGA and generates links without third-party progress bars."""
    links = []
    files = []
    
    for dirpath, dirnames, filenames in os.walk(folder_path):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            relative_path = os.path.relpath(file_path, folder_path)
            current_root_path = os.path.join(root_path, relative_path)
            files.append((file_path, current_root_path))
    
    total = len(files)
    print(f"Uploading {total} files from folder...")
    for idx, (file_path, current_root_path) in enumerate(files, 1):
        upload_info = upload_and_generate_info(login_cookie, file_path, current_root_path, email, password)
        links.append(upload_info)
        path_keeper_server(upload_info[2], [upload_info[0], upload_info[1], upload_info[3]], 'SERVER_PATHS.txt')
        path_keeper(upload_info[2], 'SERVER.txt')
        path_keeper_server(upload_info[2], upload_info[3], 'SERVER_PATHS_DOWNLOAD.txt')
        print(f"  [{idx}/{total}] Uploaded: {current_root_path}")
    
    return links

def create_folder_if_not_exists(login_cookie, folder_path):
    """Checks if the folder exists on MEGA, and creates it if not."""
    if not mega:
        return None
    folder = mega.find(folder_path)
    if not folder:
        folder = mega.create_folder(folder_path)
    return folder

def split_large_file(file_path, chunk_size=19 * 1024 * 1024 * 1024):
    """Splits large files into smaller parts using standard streaming reads."""
    file_parts = []
    with open(file_path, 'rb') as f:
        part_number = 1
        while chunk := f.read(chunk_size):
            part_name = f"{file_path}.part{part_number}"
            with open(part_name, 'wb') as part_file:
                part_file.write(chunk)
            file_parts.append(part_name)
            part_number += 1
    return file_parts

def _part_sort_key(path_str):
    """Extract numeric suffix for proper ordering (e.g. part1, part2, ..., part10)."""
    match = re.search(r'\.part(\d+)$', str(path_str))
    if match:
        return int(match.group(1))
    return str(path_str)

def join_parts(parts, output_path, buffer_size=1024 * 1024):
    """
    Reassembles .partN files in numeric order into output_path using streaming reads.
    Pure standard library: does not load entire files into memory.
    """
    sorted_parts = sorted(parts, key=_part_sort_key)
    with open(output_path, 'wb') as outfile:
        for part in sorted_parts:
            with open(part, 'rb') as partfile:
                while True:
                    chunk = partfile.read(buffer_size)
                    if not chunk:
                        break
                    outfile.write(chunk)
    return output_path

def download_file_from_url(url, download_path):
    """
    Downloads a file from a URL using standard Python urllib (no external requests library).
    Streams chunks directly to disk.
    """
    try:
        with urllib.request.urlopen(url) as response, open(download_path, 'wb') as f:
            while chunk := response.read(8192):
                f.write(chunk)
        print(f"Downloaded: {download_path}")
        return download_path
    except Exception as e:
        return f"Error downloading file: {e}"

def main(file_path, target_path='root', url=None, encrypt=False):
    print('Welcome to MEGA file uploader')
    
    if url:
        file_path = download_file_from_url(url, 'temp_downloaded_file')
        if file_path.startswith("Error"):
            print(file_path)
            return
    
    if not os.path.exists(file_path):
        print("The specified path does not exist. Please check and try again.")
        return
    
    # Opt-in client-side encryption before upload
    actual_upload_path = file_path
    if encrypt and not os.path.isdir(file_path):
        encrypted_path = f"{file_path}.enc"
        print("Encrypting file with AES-256-GCM before upload...")
        encrypt_file(file_path, encrypted_path)
        actual_upload_path = encrypted_path
        print(f"File encrypted to: {encrypted_path}")

    # Read account credentials JSON
    json_file = 'mega_credentials.json'
    if not os.path.exists(json_file):
        print("The JSON file does not exist. Please check and try again.")
        return
    
    email_password = find_account_with_sufficient_storage(json_file, actual_upload_path)
    if isinstance(email_password, str):
        print(email_password)
        return
    
    login_cookie = login_to_mega(email_password[0], email_password[1])
    if not login_cookie:
        print("Failed to log in to MEGA.")
        return
    
    # Check if target folder exists
    folder_path = target_path
    if folder_path != 'root':
        create_folder_if_not_exists(login_cookie, folder_path)
    
    root_path = os.path.join(folder_path, get_file_name(actual_upload_path))
    
    # If folder, upload all files
    if os.path.isdir(actual_upload_path):
        print("Uploading folder...")
        upload_links = upload_folder(login_cookie, actual_upload_path, root_path, email_password[0], email_password[1])
        print("Folder uploaded successfully!")
    
    # If large file, split and upload
    elif file_size(actual_upload_path) > 19 * 1024 * 1024 * 1024:  # 19GB
        print("File is too large, splitting into smaller parts...")
        file_parts = split_large_file(actual_upload_path)
        for part in file_parts:
            upload_info = upload_and_generate_info(login_cookie, part, root_path, email_password[0], email_password[1])
            print(f"Uploaded part: {upload_info[3]}")
        print("Large file uploaded successfully!")
    
    # Standard file upload
    else:
        print("Uploading file...")
        upload_info = upload_and_generate_info(login_cookie, actual_upload_path, root_path, email_password[0], email_password[1])
        path_keeper_server(upload_info[2], [upload_info[0], upload_info[1], upload_info[3]], 'SERVER_PATHS.txt')
        path_keeper(upload_info[2], 'SERVER.txt')
        path_keeper_server(upload_info[2], upload_info[3], 'SERVER_PATHS_DOWNLOAD.txt')
        print(f"File uploaded successfully! Link: {upload_info[3]}")

    # Clean up temporary URL file
    if url and os.path.exists('temp_downloaded_file'):
        os.remove('temp_downloaded_file')

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Upload:   python FINAL_SINGLE_SERVER.py <file_path> [target_path] [url] [--encrypt]")
        print("  Download: python FINAL_SINGLE_SERVER.py --download <output_path> <part1> <part2> ...")
        print("  Decrypt:  python FINAL_SINGLE_SERVER.py --decrypt <encrypted_file> [output_file]")
        sys.exit(0)

    # CLI command routing
    if sys.argv[1] == "--download":
        if len(sys.argv) < 4:
            print("Usage: python FINAL_SINGLE_SERVER.py --download <output_path> <part1> <part2> ...")
            sys.exit(1)
        out_path = sys.argv[2]
        part_files = sys.argv[3:]
        print(f"Reassembling {len(part_files)} parts into {out_path}...")
        join_parts(part_files, out_path)
        print(f"Successfully reassembled: {out_path}")
        sys.exit(0)

    if sys.argv[1] == "--decrypt":
        if len(sys.argv) < 3:
            print("Usage: python FINAL_SINGLE_SERVER.py --decrypt <encrypted_file> [output_file]")
            sys.exit(1)
        enc_file = sys.argv[2]
        dec_file = sys.argv[3] if len(sys.argv) > 3 else (enc_file[:-4] if enc_file.endswith(".enc") else f"{enc_file}.dec")
        print(f"Decrypting {enc_file} to {dec_file}...")
        decrypt_file(enc_file, dec_file)
        print(f"Successfully decrypted: {dec_file}")
        sys.exit(0)

    encrypt_flag = "--encrypt" in sys.argv
    clean_args = [a for a in sys.argv[1:] if a != "--encrypt"]
    
    file_path = clean_args[0].strip("\\/")
    target_path = clean_args[1].strip("\\/") if len(clean_args) > 1 else 'root'
    url = clean_args[2] if len(clean_args) > 2 else None
    
    main(file_path, target_path, url, encrypt=encrypt_flag)
