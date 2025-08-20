# Running Multiple Instances

The Cursor Automation System now supports multiple instances by default. Each instance operates independently without interfering with other running instances.

## Multiple Instances (Default Behavior)

```bash
python cursor.py
```

This will:
- Start a new instance without affecting existing ones
- Allow multiple instances to run simultaneously
- Each instance operates independently

## Use Cases for Multiple Instances

### ✅ **Recommended Scenarios:**
- **Testing Different Configurations**: Run multiple instances with different timer settings
- **Different Prompt Lists**: Each instance working on different prompt files  
- **Separate Projects**: Independent automation tasks for different projects
- **Development/Testing**: One instance for production use, another for testing

### ⚠️ **Caution Scenarios:**
- **Same Target Application**: Multiple instances targeting the same application window may conflict
- **Shared Resources**: Instances using the same prompt files may cause file locking issues
- **Coordinate Conflicts**: Multiple instances with overlapping click coordinates

## Best Practices

### 1. **Separate Working Directories**
```bash
# Terminal 1
cd /path/to/project1
python cursor.py --allow-multiple

# Terminal 2  
cd /path/to/project2
python cursor.py --allow-multiple
```

### 2. **Different Prompt Files**
- Use different prompt list files for each instance
- Avoid editing the same prompt file from multiple instances

### 3. **Non-Overlapping Coordinates**
- Configure different click coordinates for each instance
- Test coordinate separation to avoid conflicts

### 4. **Resource Management**
- Monitor system resources when running multiple instances
- Each instance uses its own memory and CPU

## Command Line Help

```bash
python cursor.py --help
```

Output:
```
usage: cursor.py [-h] [--allow-multiple]

Cursor Automation System

options:
  -h, --help        show this help message and exit
  --allow-multiple  Allow multiple instances to run simultaneously
```

## Troubleshooting

### **Instance Not Starting**
If an instance fails to start:
1. Check for error messages in the terminal
2. Ensure all dependencies are installed
3. Verify the working directory contains required files

### **Performance Issues**
If experiencing slowdowns with multiple instances:
1. Reduce the number of concurrent instances
2. Increase delays between automation cycles
3. Monitor system resources (CPU, memory)

### **File Conflicts**
If experiencing file access issues:
1. Use separate prompt files for each instance
2. Avoid concurrent edits to the same configuration files
3. Check file permissions

## Technical Details

The single-instance enforcement works by:
1. Using `psutil` to scan running processes
2. Identifying Python processes with `cursor.py` in command line
3. Terminating matching processes before starting new instance

The `--allow-multiple` flag simply skips this cleanup step, allowing natural multi-instance operation.
