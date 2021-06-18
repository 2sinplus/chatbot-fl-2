#

def check_manufacturer_text(text):
    if len(text) > 30:
        return False
    return True


def check_taste_text(text):
    if len(text) > 30:
        return False
    return True


def check_name_text(text):
    if len(text) > 30:
        return False
    return True


def check_address_text(text):
    if len(text) > 40:
        return False
    return True


def check_some_text(text):
    if len(text) > 128:
        return False
    return True
