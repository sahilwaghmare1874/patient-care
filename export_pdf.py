import os
import subprocess
import sys

def convert_pptx_to_pdf():
    pptx_path = os.path.abspath('Project_Final_Presentation.pptx')
    pdf_path = os.path.abspath('Project_Final_Presentation.pdf')
    
    ps_script = f"""
    $ppt = New-Object -ComObject PowerPoint.Application
    $pres = $ppt.Presentations.Open('{pptx_path}', [Microsoft.Office.Core.MsoTriState]::msoTrue, [Microsoft.Office.Core.MsoTriState]::msoFalse, [Microsoft.Office.Core.MsoTriState]::msoFalse)
    Write-Host "Slides count:" $pres.Slides.Count
    $pres.SaveAs('{pdf_path}', 32)
    $pres.Close()
    $ppt.Quit()
    [System.GC]::Collect()
    [System.GC]::WaitForPendingFinalizers()
    """
    
    script_file = 'export_script.ps1'
    with open(script_file, 'w', encoding='utf-8') as f:
        f.write(ps_script)
        
    try:
        res = subprocess.run(['powershell', '-ExecutionPolicy', 'Bypass', '-File', script_file], capture_output=True, text=True, check=True)
        print(res.stdout)
        if os.path.exists(pdf_path):
            print(f"Successfully converted to PDF: {pdf_path} (Size: {os.path.getsize(pdf_path)} bytes)")
        else:
            print("PDF file was not created.")
    except subprocess.CalledProcessError as e:
        print("Error during conversion:", e.stderr)
    finally:
        if os.path.exists(script_file):
            os.remove(script_file)

if __name__ == '__main__':
    convert_pptx_to_pdf()
