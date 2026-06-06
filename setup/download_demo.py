# setup/download_demo.py
import urllib.request
import zipfile
from pathlib import Path

DEMO_URLS = {
    "E_coli_MG1655_sensitive": "https://ftp.ncbi.nlm.nih.gov/genomes/all/GCF/000/005/845/GCF_000005845.2_ASM584v2/GCF_000005845.2_ASM584v2_genomic.fna.gz",
    "Salmonella_enterica_resistant": "https://ftp.ncbi.nlm.nih.gov/genomes/all/GCF/000/006/945/GCF_000006945.2_ASM694v2/GCF_000006945.2_ASM694v2_genomic.fna.gz",
    "Vibrio_parahaemolyticus_MDR": "https://ftp.ncbi.nlm.nih.gov/genomes/all/GCF/000/196/095/GCF_000196095.1_ASM19609v1/GCF_000196095.1_ASM19609v1_genomic.fna.gz"
}

def download_demo():
    dest_dir = Path(__file__).parent.parent / "data" / "demo"
    dest_dir.mkdir(parents=True, exist_ok=True)
    for name, url in DEMO_URLS.items():
        gz_path = dest_dir / (name + ".fna.gz")
        out_path = dest_dir / (name + ".fna")
        if out_path.exists():
            print(f"{name} 已存在，跳过")
            continue
        print(f"下载 {name} ...")
        urllib.request.urlretrieve(url, gz_path)
        # 解压
        import gzip, shutil
        with gzip.open(gz_path, 'rb') as f_in:
            with open(out_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        gz_path.unlink()  # 删除压缩包
    print("所有演示基因组准备完毕。")

if __name__ == "__main__":
    download_demo()