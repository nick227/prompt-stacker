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

## 🛠️ Installation

### Option 1: From GitHub Repository

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/prompt-stacker.git
   cd prompt-stacker
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the automation**:
   ```bash
   python automator.py
   ```

### Option 2: From Local Files

1. **Download or extract** the project files
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Run the automation**:
   ```bash
   python automator.py
   ```

### Option 3: Install as Package

```bash
pip install prompt-stacker
prompt-stacker
```

## 🎯 Quick Start

1. **Launch the application** - A beautiful Monokai-themed dialog will appear
2. **Set coordinates** - Click "Capture" buttons to set Input, Submit, and Accept positions
3. **Configure timers** - Adjust Start delay, Main wait, and Cooldown times
4. **Click Start** - The automation will begin with a countdown
5. **Monitor progress** - Watch the real-time countdown and progress bar
6. **Control execution** - Use Pause, Next, Retry, or Cancel as needed

## 📁 Project Structure

```
├── automator.py          # Main automation engine
├── ui_session.py         # Beautiful Monokai-themed UI
├── win_focus.py          # Window management and focus
├── settings_store.py     # Settings persistence
├── dpi.py               # DPI awareness for high-res displays
├── code_report_card.py  # Sample prompt data
├── requirements.txt     # Dependencies
└── coords.json         # Saved coordinates (auto-generated)
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
Edit `code_report_card.py` or create your own prompt file:
```python
my_prompts = [
    "Your first prompt here",
    "Your second prompt here",
    # ... more prompts
]
```

### Changing Target Application
Modify the window title pattern in `win_focus.py`:
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
   - Check the window title pattern in `win_focus.py`

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

## 🚀 Setting Up GitHub Repository

### Quick Setup

1. **Run the setup script**:
   ```bash
   # On Linux/Mac:
   chmod +x scripts/setup_repo.sh
   ./scripts/setup_repo.sh
   
   # On Windows (PowerShell):
   .\scripts\setup_repo.ps1
   ```

2. **Create GitHub repository**:
   - Go to [GitHub](https://github.com) and create a new repository named `prompt-stacker`
   - Don't initialize with README, .gitignore, or license (we already have these)

3. **Connect and push**:
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/prompt-stacker.git
   git push -u origin main
   ```

### Manual Setup

If you prefer to set up manually:

```bash
# Initialize git repository
git init

# Add all files
git add .

# Create initial commit
git commit -m "feat: Initial commit - Prompt Stacker automation system"

# Create main branch
git branch -M main

# Add remote and push
git remote add origin https://github.com/YOUR_USERNAME/prompt-stacker.git
git push -u origin main
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

For detailed contribution guidelines, see [CONTRIBUTING.md](CONTRIBUTING.md).

## 📄 License

This project is open source and available under the MIT License.

---

**Ready to automate! 🚀**
