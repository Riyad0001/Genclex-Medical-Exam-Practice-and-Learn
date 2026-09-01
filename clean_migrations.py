import os
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APPS_DIR = os.path.join(BASE_DIR, "apps")


def delete_migrations(app_path):
    migrations_path = os.path.join(app_path, "migrations")

    if not os.path.exists(migrations_path):
        return

    for file in os.listdir(migrations_path):
        file_path = os.path.join(migrations_path, file)

        if file == "__init__.py":
            continue

        if file.endswith(".py") or file.endswith(".pyc"):
            os.remove(file_path)
            print(f"Deleted file: {file_path}")

        elif os.path.isdir(file_path):
            shutil.rmtree(file_path)
            print(f"Deleted folder: {file_path}")


def delete_pycache(root_dir):
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for dirname in dirnames:
            if dirname == "__pycache__":
                cache_path = os.path.join(dirpath, dirname)
                shutil.rmtree(cache_path)
                print(f"Deleted __pycache__: {cache_path}")


def main():
    if not os.path.exists(APPS_DIR):
        print("apps/ directory not found!")
        return

    for app_name in os.listdir(APPS_DIR):
        app_path = os.path.join(APPS_DIR, app_name)

        if os.path.isdir(app_path):
            delete_migrations(app_path)

    delete_pycache(BASE_DIR)

    print("Cleanup completed successfully!")


if __name__ == "__main__":
    main()
