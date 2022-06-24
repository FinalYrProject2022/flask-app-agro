def chilli_logic(final_output):
    disease =""
    a = [final_output[0][0], final_output[0][1], final_output[0][2], final_output[0][3]]
    for i in range(len(a)):
        if a[i] > 0.90:
            disease = disease + names_chilli(i+1)
    if disease == "":
        disease = names_chilli(a.index(max(a))+1)
    return disease

def names_chilli(max_index):
    if max_index == 1:
        return "Fusarium Wilt, "
    if max_index == 2:
        return "Healthy, "
    if max_index == 3:
        return "Leaf Curl, "
    if max_index == 4:
        return "Leaf Spots, "