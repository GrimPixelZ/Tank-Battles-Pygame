# load save data
save_data_file = open("save_data.save", "r+")

# convert save data into usable format

save_data = {}

for line in save_data_file.readlines():
    split_line = str.split(line, "=")
    key = split_line[0]
    value = split_line[1]

    save_data[key] = value

# applies any changes to save data to the file
def update_save():
    lines = []
    for key in save_data:
        value = save_data[key]
        # must be string for concatenation
        line = key+"="+str(value)
        lines.append(line)
    save_data_file.seek(0) # goes back to start of file (to overwrite)
    save_data_file.writelines(lines)

# resets the save data to its original state
def reset_save():
    lines = [
        "high_score=0"
    ]
    save_data_file.seek(0) # goes back to start of file (to overwrite)
    save_data_file.writelines(lines)