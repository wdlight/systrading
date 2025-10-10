# Mermaid Rendering Test

## Test 1: Simple Graph (Should work)
```mermaid
graph LR
    A[Start] --> B[End]
```

## Test 2: With BR tags (May fail in older Mermaid)
```mermaid
graph LR
    A[Line 1<br/>Line 2] --> B[End]
```

## Test 3: With Korean (Should work)
```mermaid
graph LR
    A[시작] --> B[끝]
```

## Test 4: With Special Characters
```mermaid
graph LR
    A[WebSocket/API] --> B[Data Layer]
```

## Test 5: Complex Subgraph
```mermaid
graph TB
    subgraph "Frontend"
        A[Component A]
        B[Component B]
    end

    subgraph "Backend"
        C[API]
        D[Database]
    end

    A --> C
    B --> C
    C --> D
```

## Test 6: Class Diagram
```mermaid
classDiagram
    class User {
        +String name
        +int age
        +login()
    }

    class Admin {
        +String permissions
        +manage()
    }

    User <|-- Admin
```

## Test 7: Sequence Diagram
```mermaid
sequenceDiagram
    actor User
    participant A as Frontend
    participant B as Backend

    User->>A: Request
    A->>B: API Call
    B-->>A: Response
    A-->>User: Display
```
