md mm
$ProgressPreference = 'SilentlyContinue'
$d=20201215  # known to work
$url="https://valelab4.ucsf.edu/~MM/nightlyBuilds/2.0.0-gamma/Windows/MMSetup_64bit_2.0.0-gamma1_$d.exe"
Invoke-WebRequest -Uri $url -OutFile .\mm\mm.exe
.\mm\mm.exe /VERYSILENT /SUPPRESSMSGBOXES /NORESTART /DIR=".\mm\Micro-Manager"
Write-Host "done"
