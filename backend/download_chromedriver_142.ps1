# Download ChromeDriver for Chrome 142
$downloadUrl = "https://storage.googleapis.com/chrome-for-testing-public/142.0.7444.59/win64/chromedriver-win64.zip"

Write-Host "Downloading ChromeDriver 142..."
Invoke-WebRequest -Uri $downloadUrl -OutFile ".\drivers\chromedriver_142.zip"

Write-Host "Extracting..."
Expand-Archive -Path ".\drivers\chromedriver_142.zip" -DestinationPath ".\drivers\temp\" -Force

# Move to correct location (overwrite old version)
Copy-Item -Path ".\drivers\temp\chromedriver-win64\chromedriver.exe" -Destination ".\drivers\chromedriver.exe" -Force

# Cleanup
Remove-Item ".\drivers\chromedriver_142.zip" -Force
Remove-Item ".\drivers\temp" -Recurse -Force

Write-Host "✅ ChromeDriver 142 installed!"
