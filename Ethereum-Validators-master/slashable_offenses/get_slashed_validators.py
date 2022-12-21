import csv, json

with open("slashed_validator.tsv", "r") as fd:
    rd = csv.reader(fd, delimiter="\t", quotechar='"')

    slashed_validators = []
    for row in rd:
        # validator index
        indexes = row[0]
        pos = indexes.find('(')
        if pos >= 0:
            indexes = indexes[:pos]
        index_list = indexes.split(",")
        for index in index_list:
            slashed_validators.append({
                "slashed_validator": int(index),
                "reason": row[3],
                "slot": int(row[4].replace(",","")),
                "epoch": int(row[5].replace(",",""))
            })

    with open("slashed_validator.json", "w") as out_fd:
        json.dump(slashed_validators, out_fd, indent=4)
