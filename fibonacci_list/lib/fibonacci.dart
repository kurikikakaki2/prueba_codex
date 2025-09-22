/// Utilidades para generar elementos de la sucesión de Fibonacci.
class FibonacciGenerator {
  const FibonacciGenerator();

  /// Genera una lista con los primeros [cantidad] números de Fibonacci.
  ///
  /// La función acepta únicamente valores positivos o cero. Cuando la
  /// [cantidad] es `0`, se devuelve una lista vacía. Para `cantidad` igual a
  /// `1`, el resultado es `[0]`.
  ///
  /// Lanza un [ArgumentError] si [cantidad] es negativa.
  List<int> generar(int cantidad) {
    if (cantidad < 0) {
      throw ArgumentError.value(
        cantidad,
        'cantidad',
        'La cantidad no puede ser negativa.',
      );
    }

    if (cantidad == 0) {
      return List<int>.unmodifiable(const []);
    }

    if (cantidad == 1) {
      return List<int>.unmodifiable(const [0]);
    }

    final secuencia = List<int>.filled(cantidad, 0);
    secuencia[1] = 1;

    for (var indice = 2; indice < cantidad; indice++) {
      secuencia[indice] = secuencia[indice - 1] + secuencia[indice - 2];
    }

    return List<int>.unmodifiable(secuencia);
  }
}
