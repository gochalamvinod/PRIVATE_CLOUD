# Project README

## Overview

This project was created as a test of my coding skills and aims to provide a practical solution for managing unlimited private cloud storage by utilizing multiple cloud accounts such as MEGA, Google Drive, and others. The goal is to aggregate limited storage from individual accounts into a unified, unlimited private storage system.

---

## Key Concept

### Idea Behind the Project

The concept revolves around creating and managing multiple cloud accounts, uploading files to these accounts, generating public links for the files, and integrating these links into a cohesive folder structure using a custom algorithm. This approach allows combining storage from various accounts into a seamless private drive experience.

---

## Logic Behind the Code

### Core Features

- **Cloud Storage Integration**: Files are uploaded to various cloud accounts like MEGA.
- **Public Links**: Public links for the uploaded files are generated and stored.
- **Custom Algorithms**: Personal algorithms map these links to a private folder structure.

### Implementation Details

- The local device serves as the primary drive platform.
- Folder structures and link mappings are managed using three critical and sensitive text files:

#### Sensitive Files

1. **SERVER.txt**

   - Stores the folder structure of the private drive.
   - Example:
     ```
     root/tempCodeRunnerFile.py
     ```

2. **SERVER\_PATHS.txt**

   - Maps the account and link associated with each file for modifications.
   - Example:
     ```
     root/tempCodeRunnerFile.py => ['ciwalo@ext.net', 'ciwalo@txt.net', 'https://mega.co.nz/#!yEkGWSZAvEQYCrfqBA9VC-3nH0VtTjcpWLjuk']
     ```

3. **SERVER\_PATHS\_DOWNLOAD.txt**

   - Maps folder paths to corresponding file links.
   - Example:
     ```
     root/tempCodeRunnerFile.py => https://mega.co.nz/#!yEkGWSZA!w6vtoXekYwvE-3nH0VtTjcpWLjuk
     ```

---

## Usage

1. **Set Up**:

   - Ensure cloud accounts are created and ready for use.
   - Prepare the folder structure in `SERVER.txt`.

2. **File Upload**:

   - Upload files to the respective cloud accounts.
   - Generate public links for the files.

3. **Integration**:

   - Use custom algorithms to map the folder structure and associate it with cloud links.
   - Update `SERVER_PATHS.txt` and `SERVER_PATHS_DOWNLOAD.txt` accordingly.

4. **Access Files**:

   - Navigate through the local folder structure to access integrated cloud storage seamlessly.

---

## Future Enhancements

- Automating the creation and management of multiple cloud accounts.
- Adding support for additional cloud storage providers.
- Enhancing security measures for sensitive file handling.
- Developing a user-friendly interface for managing the private drive.

---

## Disclaimer

This project involves handling sensitive data, and appropriate measures should be taken to ensure its security. Unauthorized use of cloud services or violation of their terms and conditions may result in penalties or account suspension.

---

## Credits

Developed by Gochalam vinod. For testing, learning, and innovative problem-solving in cloud storage management.

