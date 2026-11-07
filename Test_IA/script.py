import os

def filter_and_remap_labels(label_dir, target_class_id=15, new_class_id=0):
    for filename in os.listdir(label_dir):
        if not filename.endswith('.txt'):
            continue
        path = os.path.join(label_dir, filename)
        with open(path, 'r') as f:
            lines = f.readlines()
        
        # Ne garder que les lignes avec la bonne classe
        new_lines = []
        for line in lines:
            parts = line.strip().split()
            if int(parts[0]) == target_class_id:
                parts[0] = str(new_class_id)
                new_lines.append(' '.join(parts) + '\n')
        
        # Réécrire le fichier
        with open(path, 'w') as f:
            f.writelines(new_lines)

# Utilisation :
filter_and_remap_labels('/home/levraiking/Code/RoboCup-Phoenix-Team/train/labels')
filter_and_remap_labels('/home/levraiking/Code/RoboCup-Phoenix-Team/val/labels')
filter_and_remap_labels('/home/levraiking/Code/RoboCup-Phoenix-Team/verification/labels')
