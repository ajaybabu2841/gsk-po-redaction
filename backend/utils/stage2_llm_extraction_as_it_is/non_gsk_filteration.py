def filter_non_gsk_medicines(all_medicine_list, gsk_brands):
    non_gsk = []
    # gsk = []

    for medicine in all_medicine_list:
        med_upper = medicine.upper()

        is_gsk = any(brand.upper() in med_upper for brand in gsk_brands)

        if not is_gsk:
            non_gsk.append(medicine)
        # else:
        #     gsk.append(medicine)
    return non_gsk
 