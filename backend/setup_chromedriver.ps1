# Download ChromeDriver automatically
$chromeVersion = (Get-Item "C:\Program Files\Google\Chrome\Application\chrome.exe").VersionInfo.FileVersion
Write-Host "Your Chrome version: $chromeVersion"

# Get major version
$majorVersion = $chromeVersion.Split('.')[0]
Write-Host "Major version: $majorVersion"

# Download URL (for Chrome 131)
$downloadUrl = "https://storage.googleapis.com/chrome-for-testing-public/131.0.6778.87/win64/chromedriver-win64.zip"

# Create drivers folder
$driversPath = ".\drivers"
if (!(Test-Path $driversPath)) {
    New-Item -ItemType Directory -Path $driversPath
}

Write-Host "Downloading ChromeDriver..."
Invoke-WebRequest -Uri $downloadUrl -OutFile ".\drivers\chromedriver.zip"

Write-Host "Extracting..."
Expand-Archive -Path ".\drivers\chromedriver.zip" -DestinationPath ".\drivers\" -Force

# Move chromedriver.exe to root of drivers folder
Move-Item -Path ".\drivers\chromedriver-win64\chromedriver.exe" -Destination ".\drivers\chromedriver.exe" -Force

# Cleanup
Remove-Item ".\drivers\chromedriver.zip"
Remove-Item ".\drivers\chromedriver-win64" -Recurse

Write-Host "✅ ChromeDriver installed at: $driversPath\chromedriver.exe"
