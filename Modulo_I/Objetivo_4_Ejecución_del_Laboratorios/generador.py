#!/usr/bin/env python3
import itertools

output_file = "diccionario_numeros_12_digitos.txt"

print(f"Generando combinaciones con dígitos únicos y guardando en '{output_file}'...")

contador = 0
with open(output_file, "w") as f:
    # Genera todas las permutaciones de 5 dígitos distintos tomados del 0 al 9
    for a, b, c, d, e in itertools.permutations(range(10), 5):
        # Patrón: A B C C D A D D D D E C
        combinacion = f"{a}{b}{c}{c}{d}{a}{d}{d}{d}{d}{e}{c}\n"
        f.write(combinacion)
        contador += 1

print(f"¡Listo! Se guardaron {contador} combinaciones únicas en '{output_file}'.")
