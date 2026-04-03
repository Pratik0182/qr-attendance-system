# QR Attendance System - Data Flow Diagram

## Context Level DFD (Level 0)
```mermaid
graph TD
    A[Teacher] -->|Login & Generate QR| B[QR Attendance System]
    C[Student] -->|Scan QR & Submit Attendance| B
    B -->|Store Data| D[(Database)]
```

## Level 1 DFD
```mermaid
graph TD
    subgraph "Teacher Interface"
        A[Teacher Login] --> B[Teacher Dashboard]
        B --> C[Generate QR]
        B --> D[View Attendance]
        B --> E[Manual Attendance]
    end

    subgraph "Student Interface"
        F[Student Login] --> G[Scan QR Page]
        G --> H[Submit Attendance]
    end

    subgraph "System Core"
        I[QR Generator] --> J[Attendance Processor]
        J --> K[Database Manager]
        K --> L[Authentication Service]
    end

    %% Data Flows
    C --> I
    H --> J
    A --> L
    F --> L
```

## Level 2 DFDs

### Level 2: Teacher Login Process
```mermaid
graph TD
    A[Teacher Credentials] --> B[Authentication Service]
    B --> C{Valid Credentials?}
    C -->|Yes| D[Generate JWT Token]
    D --> E[Set Secure Cookie]
    E --> F[Access Teacher Dashboard]
    C -->|No| G[Return Error]
```

### Level 2: QR Generation Process
```mermaid
graph TD
    A[Teacher Request] --> B[QR Generator]
    B --> C[Generate Token]
    C --> D[Embed Metadata]
    D --> E[Encrypt Token]
    E --> F[Create QR Image]
    F --> G[Store in Database]
    G --> H[Return QR to Teacher]
```

### Level 2: Student Attendance Process
```mermaid
graph TD
    A[Student Credentials] --> B[Authentication Service]
    B --> C[Validate QR Token]
    C --> D[Check IP Address]
    D --> E[Verify Timestamp]
    E --> F[Record Attendance]
    F --> G[Store in Database]
    G --> H[Return Confirmation]
```

### Level 2: Database Operations
```mermaid
graph TD
    subgraph "User Management"
        A[Create User] --> B[Store User Data]
        C[Update User] --> B
        D[Delete User] --> B
    end

    subgraph "Course Management"
        E[Create Course] --> F[Store Course Data]
        G[Update Course] --> F
        H[Delete Course] --> F
    end

    subgraph "Attendance Records"
        I[Record Attendance] --> J[Store Attendance]
        K[Update Attendance] --> J
        L[Delete Attendance] --> J
    end

    subgraph "QR Management"
        M[Create QR] --> N[Store QR Data]
        O[Update QR] --> N
        P[Delete QR] --> N
    end
```

## Data Flow Descriptions

### Level 0 Data Flows
1. Teacher → System
   - Input: Teacher credentials
   - Output: Access to teacher interface

2. Student → System
   - Input: Student credentials and QR token
   - Output: Attendance confirmation

3. System → Database
   - Input: All system data
   - Output: Data persistence

### Level 1 Data Flows
1. Teacher Login → Authentication
   - Input: Username, password
   - Output: JWT token

2. QR Generator → Database
   - Input: QR token, metadata
   - Output: Stored QR record

3. Student Attendance → Database
   - Input: Attendance record
   - Output: Stored attendance

### Level 2 Data Flows
1. Authentication Service
   - Input: Credentials
   - Output: JWT token

2. QR Generation
   - Input: Course details, timestamp
   - Output: Encrypted QR code

3. Attendance Recording
   - Input: QR token, student info
   - Output: Attendance confirmation

## External Entities
1. Teachers - System users who generate QR codes and manage attendance
2. Students - System users who scan QR codes and submit attendance
3. Database - Persistent storage for all system data

## Data Stores
1. Users - Stores teacher and student profiles
2. Courses - Stores course information and QR metadata
3. Attendance - Stores attendance records
4. QR Codes - Stores QR token information and expiry data
