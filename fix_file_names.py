import os
import re

def fix_userbot_names_precisely():
    """
    Precisely finds the 'UserBot' class in a file, extracts its specific
    bot name, and then renames the folder and file to match.
    """
    bots_dir = 'bots'
    if not os.path.isdir(bots_dir):
        print(f"Error: Directory '{bots_dir}' not found. Run from your project root.")
        return

    print("🤖 Precisely targeting 'UserBot' classes to fix names...")

    # Use a static list since we are renaming the folders
    for folder_name in list(os.listdir(bots_dir)):
        folder_path = os.path.join(bots_dir, folder_name)

        if not os.path.isdir(folder_path):
            continue

        bot_filepath = None
        for filename in os.listdir(folder_path):
            if filename.endswith('.py'):
                bot_filepath = os.path.join(folder_path, filename)
                break
        
        if not bot_filepath:
            print(f"🟡 No Python file in '{folder_name}'.")
            continue

        try:
            with open(bot_filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            # Isolate the UserBot class block to avoid confusion with other classes
            userbot_class_match = re.search(r"class\s+UserBot\s*\(\s*Bot\s*\):([\s\S]*)", content)
            
            if not userbot_class_match:
                print(f"✅ Skipping '{folder_name}' (Not a UserBot).")
                continue

            userbot_content = userbot_class_match.group(1)

            # Now, find the name ONLY within the UserBot class
            name_match = re.search(
                r"super\(\)\.__init__\s*\(\s*\"([^\"]*)\"\)|self\.name\s*=\s*\"([^\"]*)\"",
                userbot_content
            )

            if not name_match:
                print(f"⚠️ Could not find bot name inside the UserBot class for '{folder_name}'.")
                continue

            name_from_file = name_match.group(1) or name_match.group(2)
            standardized_name = name_from_file.replace('-', '_').replace(' ', '_').replace('.', '_')

            # --- 1. Fix the Filename ---
            new_filepath = os.path.join(folder_path, f"{standardized_name}.py")
            if bot_filepath != new_filepath:
                print(f"📄 FILE:   '{os.path.basename(bot_filepath)}' -> '{standardized_name}.py'")
                os.rename(bot_filepath, new_filepath)

            # --- 2. Fix the Folder Name ---
            new_folder_path = os.path.join(bots_dir, standardized_name)
            if folder_path != new_folder_path:
                # Check for conflicts before renaming
                if os.path.exists(new_folder_path):
                    print(f"❌ ERROR: Cannot rename '{folder_name}' to '{standardized_name}' because a folder with that name already exists. Please resolve duplicate bot names manually.")
                    continue
                print(f"📁 FOLDER: '{folder_name}' -> '{standardized_name}'")
                os.rename(folder_path, new_folder_path)

        except Exception as e:
            print(f"❌ Error processing folder '{folder_name}': {e}")

if __name__ == '__main__':
    fix_userbot_names_precisely()
    print("\n🎉 Script finished. All UserBot files and folders should now be correctly named.")