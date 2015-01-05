from abbreviations import bart_abbreviations, city_abbreviations

LCD_WIDTH = 16
LCD_HEIGHT = 2


try:
    from Adafruit_CharLCDPlate import Adafruit_CharLCDPlate as LCD
    lcd = LCD()
except ImportError:
    import mocklcd as lcd


def message(message):
    lcd.clear()
    lcd.message(message)


def clear():
    lcd.clear()


def off():
    lcd.clear()
    lcd.noDisplay()


def squish_text(text):
    squishes = 0
    while len(text) > LCD_WIDTH:
        if squishes == 0:
            for abbrev_dict in [bart_abbreviations, city_abbreviations]:
                for k, v in abbrev_dict.iteritems():
                    text = text.replace(k, v)
        elif squishes == 1:
            text = text.replace('To ', '')
            text = text.replace('to ', '')
        elif squishes == 2:
            text = text.replace(' ', '')
        else:
            text = text[:LCD_WIDTH]
        squishes += 1

    return text


def display_on_lcd(text_rows):
    squished_rows = []
    for row in text_rows[:LCD_HEIGHT]:
        if len(row) > LCD_WIDTH:
            squished_rows.append(squish_text(row)[:LCD_WIDTH])
        else:
            squished_rows.append(row.center(LCD_WIDTH))
    lcd.message("\n".join(squished_rows[:LCD_HEIGHT]))
