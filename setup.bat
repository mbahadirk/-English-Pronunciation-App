echo Setting Up The English Pronunciation App..

echo IMPORTANT: This app requires FFMPEG to be installed and in your system PATH for OpenAI Whisper to work.
echo If you haven't installed it, please download from https://ffmpeg.org/download.html
echo.

echo Checking/Installing PyTorch (CPU version) for Windows...
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

echo Ensuring compatible NumPy version...
pip install "numpy<2"

echo Installing other dependencies...
pip install -r requirements.txt

echo run "run_app.bat" to start application