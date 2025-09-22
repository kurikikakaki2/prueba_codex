import 'package:fibonacci_list/fibonacci.dart';
import 'package:test/test.dart';

void main() {
  group('FibonacciGenerator', () {
    final generador = const FibonacciGenerator();

    test('devuelve una lista vacía cuando la cantidad es 0', () {
      expect(generador.generar(0), isEmpty);
    });

    test('devuelve la secuencia correcta para los primeros 7 elementos', () {
      expect(
        generador.generar(7),
        equals(<int>[0, 1, 1, 2, 3, 5, 8]),
      );
    });

    test('lanza un error cuando la cantidad es negativa', () {
      expect(() => generador.generar(-1), throwsArgumentError);
    });
  });
}
