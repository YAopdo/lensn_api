import os
import base64
import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from optiland import optic
from optiland.materials import AbbeMaterial
from optiland import analysis, mtf, optic, psf, wavefront
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def download_zmx_file(efl, f_number, hfov, output_dir="lensnet_files"):
    base_url = "https://lensnet.herokuapp.com/"
    param_key = (round(efl, 2), round(f_number, 2), round(hfov, 2))
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")               # run without a UI
    chrome_options.add_argument("--no-sandbox")             # required in most containers
    chrome_options.add_argument("--disable-dev-shm-usage")  # keeps Chrome from using /dev/shm
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.binary_location = "/usr/bin/google-chrome"   # path we installed in Dockerfile
    
    # Use the chromedriver that apt installed for us; no runtime download needed
    driver = webdriver.Chrome(options=chrome_options)


    print(f"🔄 Downloading ZMX for EFL={efl}, F#={f_number}, HFOV={hfov}")
    driver.get(base_url)

    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "efl")))
        driver.find_element(By.NAME, "efl").clear()
        driver.find_element(By.NAME, "efl").send_keys(str(efl))

        driver.find_element(By.NAME, "f_number").clear()
        driver.find_element(By.NAME, "f_number").send_keys(str(f_number))

        driver.find_element(By.NAME, "hfov").clear()
        driver.find_element(By.NAME, "hfov").send_keys(str(hfov))

        driver.find_element(By.CSS_SELECTOR, 'input[type="submit"]').click()

        WebDriverWait(driver, 15).until(EC.presence_of_all_elements_located((By.LINK_TEXT, "Zemax file")))

        folder_name = f"{output_dir}/efl_{efl}_fnum_{f_number}_hfov_{hfov}"
        os.makedirs(folder_name, exist_ok=True)

        for link in driver.find_elements(By.TAG_NAME, "a"):
            href = link.get_attribute("href")
            if href.startswith("data:text/plain;base64,") and "Zemax" in link.text:
                data = base64.b64decode(href.split(",", 1)[1])
                zmx_path = os.path.join(folder_name, "design_1.zmx")
                with open(zmx_path, "wb") as f:
                    f.write(data)
                print("✅ Download complete")
                return zmx_path

        raise Exception("Zemax file not found.")
    finally:
        driver.quit()

def parse_zmx_and_create_optic(zmx_path):
    with open(zmx_path, "r") as f:
        lines = f.readlines()

    lens = optic.Optic()
    aperture_value = 5.0
    wavelengths = []
    yflns = []

    index = radius = thickness = n = abbe = None

    for line in lines:
        line = line.strip()

        if line.startswith("ENPD"):
            aperture_value = float(line.split()[1])
        elif line.startswith("WAVL"):
            wavelengths = list(map(float, line.split()[1:]))
        elif line.startswith("YFLN"):
            yflns = list(map(float, line.split()[1:]))
        elif line.startswith("SURF"):
            if index is not None and radius is not None and thickness is not None:
                if n is not None and abbe is not None:
                    if index == 1:
                        lens.add_surface(index=index, radius=radius, thickness=thickness,
                                         material=AbbeMaterial(n=n, abbe=abbe), is_stop=True)
                    else:
                        lens.add_surface(index=index, radius=radius, thickness=thickness,
                                         material=AbbeMaterial(n=n, abbe=abbe))
                else:
                    if index == 1:
                        lens.add_surface(index=index, radius=radius, thickness=thickness, is_stop=True)
                    else:
                        lens.add_surface(index=index, radius=radius, thickness=thickness)

            index = int(line.split()[1])
            radius = thickness = n = abbe = None

        elif line.startswith("CURV"):
            curv = float(line.split()[1])
            radius = np.inf if curv == 0 else 1.0 / curv
        elif line.startswith("DISZ"):
            val = line.split()[1]
            thickness = np.inf if val == "INFINITY" else float(val)
        elif line.startswith("GLAS"):
            parts = line.split()
            n = float(parts[4])
            abbe = float(parts[5])

    # Add final surface
    if index is not None and radius is not None and thickness is not None:
        if n is not None and abbe is not None:
            if index == 1:
                lens.add_surface(index=index, radius=radius, thickness=thickness,
                                 material=AbbeMaterial(n=n, abbe=abbe), is_stop=True)
            else:
                lens.add_surface(index=index, radius=radius, thickness=thickness,
                                 material=AbbeMaterial(n=n, abbe=abbe))
        else:
            if index == 1:
                lens.add_surface(index=index, radius=radius, thickness=thickness, is_stop=True)
            else:
                lens.add_surface(index=index, radius=radius, thickness=thickness)

    # Final dummy/image surface
    lens.add_surface(index=index + 1)

    # Set aperture
    lens.set_aperture(aperture_type="EPD", value=aperture_value)

    # Set fields from YFLN
    lens.set_field_type("angle")
    if yflns:
        for y in yflns:
            lens.add_field(y=y)
    else:
        lens.add_field(y=0)

    # Set wavelengths
    for i, w in enumerate(wavelengths):
        lens.add_wavelength(value=w, is_primary=(i == 1))

    return lens

if __name__ == "__main__":
    efl = 2
    f_number = 2
    hfov = 2

    zmx_path = download_zmx_file(efl, f_number, hfov)
    lens = parse_zmx_and_create_optic(zmx_path)
    lens.draw(num_rays=10)
    plt.savefig('1.png', dpi=300)
    plt.close()
    distortion = analysis.Distortion(lens)
    distortion.view()
    plt.savefig('2.png', dpi=300)
    plt.close()
    fan = analysis.RayFan(lens)
    fan.view()
    plt.savefig('3.png', dpi=300)
    plt.close()
