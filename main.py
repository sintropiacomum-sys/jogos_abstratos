import time
from games import connect6, pente, othello, pentago, pentwiste, breakthrough

CLEAR = "\033[H\033[J"

if __name__ == "__main__":

    while True:

        print(CLEAR, end="")

        print("""
        LUDOTECA DE ABSTRATOS
        \n1. Connect6
        \n2. Pente
        \n3. Othello
        \n4. Pentago
        \n5. Pentwiste
        \n6. Breakthrough""")
        print()

        try:

            choice = int(input("Escolha um dos jogos pelo seu número: "))

            if choice == 1:

                connect6.play_connect6()

            if choice == 2:

                pente.play_pente()

            if choice == 3:

                othello.play_othello()

            if choice == 4:
            
                pentago.play_pentago()

            if choice == 5:
                        
                pentwiste.play_pentwiste()

            if choice == 6:
                                    
                breakthrough.play_breakthrough()

            else:

                print("Este input não existe, tente um número dentre as opções.")
                time.sleep(2)

                continue

        except ValueError as e:

            e = print("Input irreconhecível, utilize um número inteiro.")
            time.sleep(2)