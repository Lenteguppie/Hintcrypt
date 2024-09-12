from typing import Any
import yaml
import csv
import argparse
import os
import random

# Character mapping: A-Z -> 0-25, 0-9 -> 26-35
char_map: dict[str, int] = {chr(i): i - 65 for i in range(65, 91)}  # A-Z
char_map.update({str(i): 26 + i for i in range(0, 10)})  # 0-9

# Reverse character map to go back from numbers to characters
reverse_char_map: dict[int, str] = {v: k for k, v in char_map.items()}

def load_yaml(file_path):
    with open(file_path, "r") as file:
        return yaml.safe_load(file)

def generate_random_hint(index) -> dict[str, Any]:
    shift = random.randint(-5, 5)  # Random shift between -5 and +5
    return {
        'person': '',  # Person is left blank for generated hints
        'type': 'direct',
        'shift': shift,
        'character': index,  # Use the character index
        'requirement': 'Generated random shift',  # You can adjust the requirement text
        'hint_text': f"Het {index}e teken wordt verschoven met {shift}."
    }

def ensure_sufficient_hints(activation_key, hints):
    # Create a dictionary to track which character indices are covered in the existing hints
    existing_hints = {hint['character'] for hint in hints}
    total_characters = len(activation_key)

    not_existing = []

    # Generate new hints only for the missing characters
    for i in range(1, total_characters + 1):  # 'character' field is 1-based
        if i not in existing_hints:
            not_existing.append(i)
            random_hint = generate_random_hint(index=i)
            hints.append(random_hint)


    # Sort the hints by the 'character' field
    hints.sort(key=lambda x: x['character'])

    return hints

def encrypt_key(activation_key, yaml_data):
    hints = yaml_data['hints']
    templates = yaml_data['templates']

    # Ensure there are enough hints for the length of the activation key
    hints = ensure_sufficient_hints(activation_key, hints)

    encrypted_key = []
    hint_texts = []

    for hint in hints:
        index = hint['character'] - 1  # Get the 0-based index from the 'character' field
        char = activation_key[index]
        char_value = char_map[char]  # Get numeric value of character

        if hint['type'] == 'direct':
            shift = hint['shift']
            encrypted_value = (char_value + shift) % 36  # Apply the shift
            encrypted_char = reverse_char_map[encrypted_value]  # Convert back to character
            hint_text = templates['direct'].format(
                person=hint['person'] if hint['person'] else "Onbekend",  # Use "Onbekend" (Unknown) if person is blank
                index=hint['character'],
                shift=shift,
                encrypted_char=encrypted_char
            )
        elif hint['type'] == 'relative':
            ref_person = hints[hint['reference_hint'] - 1]['person']
            ref_char_value = encrypted_key[hint['reference_hint'] - 1]
            shift = hint['extra_shift']

            if hint['extra_shift'] >= 0:
                hint_text = templates['relative_more'].format(
                    person=hint['person'] if hint['person'] else "Onbekend",  # Use "Onbekend" (Unknown) if person is blank
                    index=hint['character'],
                    extra_shift=hint['extra_shift'],
                    reference_person=ref_person
                )
            else:
                hint_text = templates['relative_less'].format(
                    person=hint['person'] if hint['person'] else "Onbekend",  # Use "Onbekend" (Unknown) if person is blank
                    index=hint['character'],
                    extra_shift=abs(hint['extra_shift']),
                    reference_person=ref_person
                )

            encrypted_value = (char_value + shift) % 36  # Apply the shift
            encrypted_char = reverse_char_map[encrypted_value]  # Convert back to character

        encrypted_key.append(encrypted_value)
        hint_texts.append((hint['person'], hint_text, hint['requirement'], encrypted_char))

    encrypted_key_str = "".join(reverse_char_map[v] for v in encrypted_key)  # Build encrypted key string
    return encrypted_key_str, hint_texts

def write_hints_to_csv(hints, encrypted_key, file_path):
    csv_file = f"hints-{encrypted_key}.csv"

    # Check if the directory exists, if not, create it
    if not os.path.exists(os.path.dirname(csv_file)):
        try:
            os.makedirs(os.path.dirname(csv_file))
        except OSError as exc:
            print(f"Error creating directory: {exc}")

    # Write the CSV file
    with open(csv_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Person', 'Hint Description', 'Requirement', 'Encrypted Character'])
        for hint in hints:
            writer.writerow(hint)

    print(f"Hints have been written to {csv_file}")

def main():
    # Parse arguments
    parser = argparse.ArgumentParser(description="Encrypt activation key and generate hint CSV")
    parser.add_argument('activation_key', type=str, help="Activation key to be encrypted")
    parser.add_argument('yaml_file', type=str, help="YAML file with hint instructions")
    args = parser.parse_args()

    # Load the YAML data
    yaml_data = load_yaml(args.yaml_file)

    # Encrypt the key and generate the hint descriptions
    encrypted_key, hint_texts = encrypt_key(args.activation_key, yaml_data)

    # Write hints to CSV
    write_hints_to_csv(hint_texts, encrypted_key, args.activation_key)

    print(f"Encrypted Key: {encrypted_key}")

if __name__ == "__main__":
    main()
