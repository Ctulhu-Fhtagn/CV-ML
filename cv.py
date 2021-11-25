import pytesseract
import cv2
import re
import json

class ComputerVision():
    #all areas where needed information
    AREAS = {
        "heading":{"x": 290, "y": 0, "w": 870, "h": 60},
        "date":{"x": 130, "y": 60, "w": 170, "h": 45},
        "number":{"x": 530, "y": 65, "w": 170, "h": 45},
        "point":{"x": 845, "y": 65, "w": 175, "h": 40},
        "name":{"x": 290, "y": 110, "w": 675, "h": 70},
        "authors":{"x": 290, "y": 165, "w": 675, "h": 60},
        "organisation":{"x": 290, "y": 200, "w": 675, "h": 65},
        "developer":{"x": 290, "y": 245, "w": 675, "h": 70},
        "referent":{"x": 290, "y": 315, "w": 675, "h": 70},
    }

    #names of points
    JSON_SCHEME = {
        'Выписка из протокола': '',
        "дата": "",
        "номер": "",
        "пункт": "",
        "Наименование объекта": "",
        "Авторы проекта": "", 
        "Генеральная проектная организация": "",
        "Застройщик": "",
        "Рассмотрение на рабочей комиссии": "",
        "Референт": "",
        "Докладчик": "",
        "Выступили": ""  
    }

    def detect_any(self, area):
        """
        detect any symbols in area, better use for words
        area: croped area from image, where numbers will be detect
        return: str
        """
        string = str(pytesseract.image_to_string(area, lang='rus', config='--dpi 100')) #with num work for 2, 3, 4;  fine for dates
        return string

    def detect_number(self, area):
        """
        detect numbers in area
        area: croped area from image, where numbers will be detect
        return: int
        """
        string = pytesseract.image_to_string(area, lang='rus', config='--psm 12 outputbase digits') #--psm 12 work for 1, 2, 4
        try:
            detected = int(string)
            return detected
        except:
            return self.detect_any(area)    
        
    def find_global_area(self, img):
        """
        find area of all blank
        img: any image for open using openCV
        return: image without white edges, only filled blank
        """
        img = cv2.imread(img)  
        d = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT, lang='rus')
        number = 0
        #start of global area
        for text in d['text']:
            if text == "ВЫПИСКА":
                for line in enumerate(d):
                    #left
                    if line[0] == 6:
                        x = d[line[1]][number]
                    #top
                    if line[0] == 7:
                        y = d[line[1]][number]
            number += 1

        number = 0
        #end of global area
        for text in d['text']:
            if text[0:9] == "Выступили":
                for line in enumerate(d):
                    #top            
                    if line[0] == 7:
                        y_last_string = d[line[1]][number]
                    #height of global area
                    if line[0] == 9:
                        h = d[line[1]][number]
                        y_end = y_last_string + h
            number += 1
        y = y - 10
        h = y_end - y
        w = 1020
        img_crop = img[y:y+h, x:x+w]
        return img_crop

    def find_surname(self, string):
        """
        search surname in input string
        string: str
        string: input string for searching in surnames
        return: list of strings
        """
        string = str(string)
        many = string.splitlines()
        for one in many:
            detected_surname = re.findall(r'[А-Я]{1}[а-яА-Я]+ [А-Я]{1}.?[А-Я]{1}', one)
            if detected_surname:
                return detected_surname

    def find_string_area(self, img, x, y, w, h):
        """
        find area of one point\string
        img: OpenCV image obj
        img: whole image
        x, y, w, h: int
        x, y: coordinates 
        x: distance from left border
        y: distance from top border
        w: vertical size of area 
        h: horizontal size of area 
        return: image of one string
        """
        img_global = self.find_global_area(img)
        string_image = img_global[y:y+h, x:x+w]
        return string_image

    def write_in_json(self, img):
        """
        Take whole image. write it into json file
        img: file *.jpg
        img: image which you need to detect
        """
        end_json = self.JSON_SCHEME
        #CREATE NAME YOUR JSON FILE
        with open("*.json", "w") as file:
            for line in self.AREAS:
                #  take coordinate of one area
                x = self.AREAS[line]["x"]
                y = self.AREAS[line]["y"]
                w = self.AREAS[line]["w"]
                h = self.AREAS[line]["h"]
                #crop image by coordinates
                get_img = self.find_string_area(img, x, y, w, h)
                
                #detect if it is a number
                if line in ["date", "number", "point"]:
                    finded = str(self.detect_number(get_img))
                #detect if it is a surname. write into string with commas
                elif line in ["authors", "referent"]:
                    finded_list = self.find_surname(self.detect_any(get_img))
                    finded = ''
                    for i in finded_list:
                        finded = finded + ', ' + i
                    finded = finded[2:]
                else:
                    finded = self.detect_any(get_img)
                
                #write to every needed json heading
                if line == "heading":
                    finded = finded.strip()
                    end_json["Выписка из протокола"] = finded.replace('\n', ' ')
                elif line == "date":
                    end_json["дата"] = finded.strip()
                elif line == "number":
                    end_json["номер"] = finded.strip()
                elif line == "point":
                    finded = finded.strip()
                    try:
                        finded = int(finded)
                    except:
                        finded = ''
                    end_json["пункт"] = str(finded)
                elif line == "name":
                    finded = finded.strip()
                    end_json["Наименование объекта"] = finded.replace('\n', ' ')
                elif line == "authors":
                    end_json["Авторы проекта"] = finded.strip()
                elif line == "organisation":
                    finded = finded.strip()
                    end_json["Генеральная проектная организация"] = finded.replace('\n', ' ')
                elif line == "developer":
                    finded = finded.strip()
                    end_json["Застройщик"] = finded.replace('\n', ' ')
                elif line == "referent":
                    end_json["Референт"] = finded.strip()
            json.dump(end_json, file, ensure_ascii=False)

        return get_img

def main():
    test = ComputerVision()
    #HERE YOU GET YOUR IMAGE
    test.write_in_json("") 

if __name__ == "__main__":
	main()
