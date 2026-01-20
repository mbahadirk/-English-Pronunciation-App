@echo off
setlocal

echo ======================================================
echo English Pronunciation App - Kurulum Baslatiliyor...
echo ======================================================

:: 1. Sanal Ortam Olusturma
if not exist "venv" (
    echo Sanal ortam bulunamadi, yeni bir venv olusturuluyor...
    python -m venv venv
    if %ERRORLEVEL% neq 0 (
        echo [HATA] Sanal ortam olusturulamadi. Python'un yuklu oldugundan emin olun.
        pause
        exit /b
    )
) else (
    echo Mevcut sanal ortam (venv) bulundu, devam ediliyor...
)

:: 2. Sanal Ortami Aktif Etme
echo Sanal ortam aktif ediliyor...
call venv\Scripts\activate

:: 3. Paketlerin Kurulumu
echo.
echo Pip guncelleniyor...
python -m pip install --upgrade pip

echo.
echo IMPORTANT: This app requires FFMPEG to be installed and in your system PATH.
echo.

echo [1/3] PyTorch (CPU version) yukleniyor...
python -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

echo [2/3] NumPy (v1.x) uyumlulugu saglaniyor...
python -m pip install "numpy<2"

echo [3/3] Diger gereklilikler yukleniyor...
if exist requirements.txt (
    python -m pip install -r requirements.txt
) else (
    echo [UYARI] requirements.txt dosyasi bulunamadi, bu adim atlaniyor.
)

echo.
echo ======================================================
echo Kurulum Basariyla Tamamlandi!
echo Uygulamayi baslatmak icin "run_app.bat" kullanabilirsiniz.
echo ======================================================
pause