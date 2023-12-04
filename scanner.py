"""
File: Scanner.py
Author: Jacob Barner & Todd Proebsting
Purpose:  This program acts as a makeshift scanner that is able to iterate through the characters
of a file and return the Tokens in the file.  Each token has a type, value and span
    type - "EOF" = End of File
           "INT" = Numeric Values
           "ID"  = Identifiers that start with letters
           "<value>" = the keyword or punctuation's value set as its id
    
    value - The string for the token.

    span  - The starting and ending coordinates of the token.

Available functions:
    Constructor(string): creates a scanner that reads through the given string of values.
    peek(): returns the first found token without moving on.
    consume(): returns the first found token and then continues on.
"""

from tau import tokens, error
from tau.tokens import Span, Coord, Token, punctuation, keywords

class Scanner:
    start_line: int
    start_col: int
    curr_index: int
    string: str
    valid_chars = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', '1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '!']

    def __init__(self, input: str):
        self.string = input
        self.start_line = 1
        self.start_col = 1
        self.curr_index = 0

    def peek(self) -> Token:
        i = self.curr_index
        temp_line = self.start_line
        temp_col = self.start_col
        start_coord = Coord(temp_col, temp_line) #creates the intitial save data for the coordinates.
        end_coord = Coord(temp_col, temp_line)
        value = ""
        id = "NULL"
        while(i <= len(self.string)): #iterates through the characters in the string until it reaches white space.
            if(i == len(self.string)  or len(self.string) == 0):
                end_coord = Coord(temp_col, temp_line)
                break
            elif(self.string[i] == " "): #ignore spaces
                if(value == ""):
                    temp_col += 1
                    start_coord = Coord(temp_col, temp_line)
                else:
                    end_coord = Coord(temp_col, temp_line)
                    temp_col += 1
                    break
            elif(self.string[i] == "\t"): #ignore tabs
                if(value == ""):
                    temp_col += 1
                    start_coord = Coord(temp_col, temp_line)
                else:
                    end_coord = Coord(temp_col, temp_line)
                    temp_col += 1
                    break
            elif(self.string[i] == "\n"): #ignore newline
                if(value == ""):
                    temp_col = 1
                    temp_line += 1
                    start_coord = Coord(temp_col, temp_line)
                else:
                    end_coord = Coord(temp_col, temp_line)
                    temp_col = 1
                    temp_line += 1
                    break
            elif(self.string[i] == "/" and self.string[i+1] == "/"): #ignore all of a comment
                if(value == ""):
                    while(self.string[i] != "\n"):
                        i += 1
                    temp_col = 1
                    temp_line += 1
                    start_coord = Coord(temp_col, temp_line)
                else:
                    end_coord = Coord(temp_col, temp_line)
                    temp_line += 1
                    temp_col = 1
                    break
            else: #otherwise add the characters to the current token's value.
                if(value == ""): #determine what kind of token it will be
                    if(self.string[i] not in self.valid_chars and self.string[i] not in tokens.punctuation):
                        temp_col += 1
                        end_coord = Coord(temp_col, temp_line)
                        error.error("Invalid Character", Span(start_coord, end_coord))
                    value += self.string[i]
                    temp_col += 1
                    if(value.isnumeric()): #determine the id of the token
                        id = "INT"
                    elif(value == "!" and self.string[i+1] == "="):
                        value += "="
                        temp_col += 1
                        id = value
                    elif(value == "<" and self.string[i+1] == "="):
                        value += "="
                        temp_col += 1
                        id = value
                    elif(value == ">" and self.string[i+1] == "="):
                        value += "="
                        temp_col += 1
                        id = value
                    elif(value == "=" and self.string[i+1] == "="):
                        value += "="
                        temp_col += 1
                        id = value
                    elif(value in tokens.punctuation):
                        id = value
                    else:
                        id = "ID"
                elif(id == value): #continue if punctuation or keyword
                    end_coord = Coord(temp_col, temp_line)
                    break
                elif((value in tokens.punctuation or value in tokens.keywords) and self.string[i] not in tokens.punctuation):
                    value += self.string[i]
                    temp_col += 1
                elif(value in tokens.punctuation or value in tokens.keywords): #makes sure the current token isnt a seperate keyword or value.
                    end_coord = Coord(temp_col, temp_line)
                    break
                elif(id == "INT" and self.string[i].isnumeric()): #make sure INT continues as INT
                    value += self.string[i]
                    temp_col += 1
                elif((id == "INT" and self.string[i].isalpha()) or (id == "INT" and self.string[i] in tokens.punctuation)): #stop if letter added to INT
                    end_coord = Coord(temp_col, temp_line)
                    break
                elif(id == "ID" and self.string[i] in tokens.punctuation): #makes sure the word being built isnt a punctuation
                    end_coord = Coord(temp_col, temp_line)
                    break
                elif(id == "ID" and self.string[i] in tokens.keywords): #makes sure the word being built isnt a keyword
                    end_coord = Coord(temp_col, temp_line)
                    break
                elif(id == "ID"): #Add to value otherwise
                    value += self.string[i]
                    temp_col += 1
                else:
                    end_coord = Coord(temp_col, temp_line)
                    break
            
            i += 1
        if(value == ""): #determines the id of the token based on its value.
            id = "EOF"
        elif(value in tokens.punctuation or value in tokens.keywords):
            id = value
        span = Span(start_coord, end_coord) #creates the token's span
        token = Token(id, value, span) #finally creates and returns the token without consuming it.
        return token

    def consume(self) -> Token: #creates the intitial save data for the coordinates.
        start_coord = Coord(self.start_col, self.start_line)
        end_coord = Coord(self.start_col, self.start_line)
        i = self.curr_index
        value = ""
        id="temp"
        while(i <= len(self.string)): #iterates through the characters in the string until it reaches white space.
            if(i == len(self.string) or len(self.string) == 0):
                end_coord = Coord(self.start_col, self.start_line)
                self.curr_index = i + 1
                break
            elif(self.string[i] == " "): #ignore spaces
                if(value == ""):
                    self.start_col += 1
                    start_coord = Coord(self.start_col, self.start_line)
                else:
                    end_coord = Coord(self.start_col, self.start_line)
                    self.start_col += 1
                    self.curr_index = i + 1
                    break
            elif(self.string[i] == "\t"): #ignore spaces
                if(value == ""):
                    self.start_col += 1
                    start_coord = Coord(self.start_col, self.start_line)
                else:
                    end_coord = Coord(self.start_col, self.start_line)
                    self.start_col += 1
                    self.curr_index = i + 1
                    break
            elif(self.string[i] == "\n"): #ignore newline
                if(value == ""):
                    self.start_line += 1
                    self.start_col = 1
                    start_coord = Coord(self.start_col, self.start_line)
                else:
                    end_coord = Coord(self.start_col, self.start_line)
                    self.start_line += 1
                    self.start_col = 1
                    self.curr_index = i + 1
                    break
            elif(self.string[i] == "/" and self.string[i+1] == "/"): #ignore all of a comment
                if(value == ""):
                    while(self.string[i] != "\n"):
                        i += 1
                    self.curr_index = i
                    self.start_line += 1
                    self.start_col = 1
                    start_coord = Coord(self.start_col, self.start_line)
                else:
                    end_coord = Coord(self.start_col, self.start_line)
                    self.start_line += 1
                    self.start_col = 1
                    self.curr_index = i + 1
                    break
            else: #otherwise add the characters to the current token's value.
                if(value == ""): #determine what kind of token it will be
                    if(self.string[i] not in self.valid_chars and self.string[i] not in tokens.punctuation):
                        self.start_col += 1
                        end_coord = Coord(self.start_col, self.start_line)
                        error.error("Invalid Character", Span(start_coord, end_coord))
                    value += self.string[i]
                    self.start_col += 1
                    if(value.isnumeric()): #determines the id of the token
                        id = "INT"
                    elif(value == "!" and self.string[i+1] == "="):
                        value += "="
                        i += 1
                        self.start_col += 1
                        id = value
                    elif(value == "<" and self.string[i+1] == "="):
                        value += "="
                        i += 1
                        self.start_col += 1
                        id = value
                    elif(value == ">" and self.string[i+1] == "="):
                        value += "="
                        i += 1
                        self.start_col += 1
                        id = value
                    elif(value == "=" and self.string[i+1] == "="):
                        value += "="
                        i += 1
                        self.start_col += 1
                        id = value
                    elif(value in tokens.punctuation):
                        id = value
                    else:
                        id = "ID"
                elif(id == value): #check for a punctuation or keyword
                    end_coord = Coord(self.start_col, self.start_line)
                    self.curr_index = i
                    break
                elif((value in tokens.punctuation or value in tokens.keywords) and self.string[i] not in tokens.punctuation):
                    value += self.string[i]
                    self.start_col += 1
                elif(value in tokens.punctuation or value in tokens.keywords): #check if value is a punctuation or keyword
                    end_coord = Coord(self.start_col, self.start_line)
                    self.curr_index = i
                    break
                elif(id == "INT" and self.string[i].isnumeric()): #make sure INT continues as INT
                    value += self.string[i]
                    self.start_col += 1
                elif((id == "INT" and self.string[i].isalpha()) or (id == "INT" and self.string[i] in tokens.punctuation)): #stop if letter added to INT
                    end_coord = Coord(self.start_col, self.start_line)
                    self.curr_index = i
                    break
                elif(id == "ID" and self.string[i] in tokens.punctuation): #ensure not completed punctuation
                    end_coord = Coord(self.start_col, self.start_line)
                    self.curr_index = i
                    break
                elif(id == "ID" and self.string[i] in tokens.keywords): #ensure not completed keyword
                    end_coord = Coord(self.start_col, self.start_line)
                    self.curr_index = i
                    break
                elif(id == "ID"): #Add to value otherwis e
                    value += self.string[i]
                    self.start_col += 1
                else:
                    end_coord = Coord(self.start_col, self.start_line)
                    break
            i += 1
            self.curr_index = i

        if(value == ""): #determines the id of the token based on its value.
            id = "EOF"
        elif(value in tokens.punctuation or value in tokens.keywords):
            id = value
        span = Span(start_coord, end_coord) #creates the token's span
        token = Token(id, value, span) #finally creates and returns the token, and consumes it.
        return token

# lines = ''.join(open('./tau/tests/m11/test10.tau', 'r').readlines())
# s = Scanner(lines)
# while(s.peek().kind != "EOF"):
#     print(s.peek())
#     s.consume()