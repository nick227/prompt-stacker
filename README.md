# 🚀 Cursor Automation System

A powerful, production-ready automation system for Cursor with a beautiful Monokai-themed UI.

## ✨ Features

- **🎯 Smart Automation**: Automated text input and button clicking for Cursor
- **🎨 Beautiful UI**: Authentic Monokai dark theme with enhanced spacing
- **⚡ Optimized Performance**: Minimal delays and efficient clipboard operations
- **🛡️ Robust Error Handling**: Comprehensive retry mechanisms and fallbacks
- **📊 Real-time Feedback**: Live countdown timers and progress indicators
- **💾 Persistent Settings**: Saves coordinates and preferences automatically
- **🎮 User Control**: Pause, skip, retry, and cancel functionality

## 🚀 Quick Start

### Run the Application

The main way to run the application is:

```bash
python cursor.py
```

### Alternative: Build Executable

If you prefer a standalone executable:

```bash
# Navigate to build tools
cd build_tools

# Build the executable
python build.py

# The executable will be created in the dist/ directory
```

## 🛠️ Installation

### Prerequisites

- **Python**: 3.8 or higher
- **OS**: Windows (primary), Linux/macOS (limited support)

### Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/prompt-stacker.git
   cd prompt-stacker
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   python cursor.py
   ```

## 🎯 Usage

1. **Launch the application** - A beautiful Monokai-themed dialog will appear
2. **Set coordinates** - Click "Capture" buttons to set Input, Submit, and Accept positions
3. **Configure timers** - Adjust Start delay, Main wait, and Cooldown times
4. **Click Start** - The automation will begin with a countdown
5. **Monitor progress** - Watch the real-time countdown and progress bar
6. **Control execution** - Use Pause, Next, Retry, or Cancel as needed

## 📁 Project Structure

```
├── cursor.py              # Main application entry point
├── src/                   # Source code
│   ├── automator.py       # Main automation engine
│   ├── ui/                # Modular UI (session_app.py, session_controller.py, prompt_io.py, state_manager.py)
│   ├── win_focus.py       # Window management and focus
│   ├── settings_store.py  # Settings persistence
│   └── dpi.py            # DPI awareness for high-res displays
├── prompt_lists/          # Prompt data files
├── build_tools/          # Build and distribution tools
├── docs/                 # Documentation
├── tests/                # Test files
├── requirements.txt      # Dependencies
└── coords.json          # Saved coordinates (auto-generated)
```

## 🎨 UI Features

- **Monokai Dark Theme**: Authentic color palette with enhanced contrast
- **Smart Button Colors**: 
  - 🟢 Green: Positive actions (Capture, Next)
  - 🟡 Yellow: Caution actions (Pause, Retry)
  - 🔴 Red: Destructive actions (Cancel)
  - 🟣 Pink: Primary actions (Start)
- **Enhanced Spacing**: Optimized layout with proper visual hierarchy
- **Real-time Feedback**: Live status updates and progress indicators
- **Process Visualization**: Step-by-step automation status with emojis
- **Get Ready Pause**: Configurable pause before each cycle with dialog to front

## ⚙️ Configuration

### Timing Settings
- **Start Delay**: Initial countdown before automation begins
- **Main Wait**: Time between prompt submissions
- **Cooldown**: Brief pause after accepting responses
- **Get Ready**: Pause before each automation cycle (default: 2s)

### Automation Settings
- **Focus Delay**: 0.05s - Minimal delay for UI focus
- **Clipboard Retry**: 3 attempts with 0.2s delays
- **PyAutoGUI Pause**: 0.1s between actions
- **Process Visualization**: Real-time status updates during automation

## 🔧 Customization

### Adding New Prompts
Edit files in `prompt_lists/` or create your own prompt file:
```python
my_prompts = [
    "Your first prompt here",
    "Your second prompt here",
    # ... more prompts
]
```

### Changing Target Application
Modify the window title pattern in `src/win_focus.py`:
```python
DEFAULT_TITLE = "Your App Name"
```

## 🐛 Troubleshooting

### Common Issues

1. **Clipboard not working**
   - Ensure no other applications are blocking clipboard access
   - Try running as administrator if needed

2. **Coordinates not accurate**
   - Ensure DPI scaling is properly configured
   - Re-capture coordinates if display settings change

3. **Window not found**
   - Verify the target application is running
   - Check the window title pattern in `src/win_focus.py`

### Logs
Check `automation.log` for detailed error information and debugging.

## 🚀 Performance

- **Optimized timing**: Minimal delays for maximum efficiency
- **Robust retry logic**: Handles temporary failures gracefully
- **Memory efficient**: Clean resource management
- **Fast UI**: Responsive interface with smooth animations

## 📋 Requirements

- **Python**: 3.8 or higher
- **OS**: Windows (primary), Linux/macOS (limited support)
- **Dependencies**: See `requirements.txt`

## 📚 Documentation

For detailed documentation, see the `docs/` directory:
- [Architecture Guide](docs/ARCHITECTURE.md)
- [Build Guide](docs/BUILD_GUIDE.md)
- [Testing Guide](docs/TESTING.md)
- [Distribution Guide](docs/DISTRIBUTION_GUIDE.md)
- [Contributing Guide](docs/CONTRIBUTING.md)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

For detailed contribution guidelines, see [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md).

## 📄 License

This project is open source and available under the MIT License.

---

**Ready to automate! 🚀**
