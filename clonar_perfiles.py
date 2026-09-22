import os
import shutil

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    profiles_dir = os.path.join(base_dir, "Profiles")
    source_profile = os.path.join(profiles_dir, "chrome_profile_0")

    if not os.path.exists(source_profile):
        print(f"❌ No se encontró el perfil base: {source_profile}")
        print("Abre primero la instancia 0 desde tu script, instala y configura la extensión de VPN y luego cierra Chrome.")
        return

    print(f"✅ Perfil base encontrado: {source_profile}")
    print("Iniciando clonación hasta el perfil 49...")

    for i in range(1, 40):
        target_profile = os.path.join(profiles_dir, f"chrome_profile_{i}")
        
        # Si ya existe, lo eliminamos para sobreescribirlo limpio
        if os.path.exists(target_profile):
            print(f"⚠️ Eliminando perfil existente: chrome_profile_{i}")
            shutil.rmtree(target_profile)
        
        # Copiamos el perfil
        shutil.copytree(source_profile, target_profile)
        print(f"📁 Clonado: chrome_profile_{i}")

    print("\n🚀 ¡Clonación de 50 perfiles completada con éxito!")

if __name__ == "__main__":
    main()
