const { app, BrowserWindow } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let pythonProcess = null;
let mainWindow = null;
let apiPort = 9080;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
    },
  });

  if (process.env.NODE_ENV === 'development') {
    mainWindow.loadURL('http://localhost:5173');
  } else {
    mainWindow.loadFile(path.join(__dirname, '../dist/index.html'));
  }
}

function startPythonServer() {
  const isPackaged = app.isPackaged;
  const pythonPath = isPackaged
    ? path.join(process.resourcesPath, 'agent-proxy/bin/agent-proxy')
    : process.platform === 'win32' ? 'python' : 'python3';

  const args = ['-m', 'agent_proxy.cli', '--server', '--port', String(apiPort)];

  const envPath = path.join(__dirname, '../../../.venv/bin/python');
  const actualPython = isPackaged ? pythonPath : envPath;

  pythonProcess = spawn(actualPython, args, {
    stdio: ['pipe', 'pipe', 'pipe'],
    cwd: path.join(__dirname, '../../../'),
  });

  pythonProcess.stdout.on('data', (data) => {
    console.log(`Python: ${data}`);
    if (data.toString().includes('API')) {
      setTimeout(createWindow, 1000);
    }
  });

  pythonProcess.stderr.on('data', (data) => {
    console.error(`Python Error: ${data}`);
  });

  pythonProcess.on('error', (err) => {
    console.error('Failed to start Python process:', err);
  });
}

app.whenReady().then(() => {
  startPythonServer();
});

app.on('window-all-closed', () => {
  if (pythonProcess) {
    pythonProcess.kill('SIGTERM');
  }
  app.quit();
});

app.on('before-quit', () => {
  if (pythonProcess) {
    pythonProcess.kill('SIGTERM');
  }
});
