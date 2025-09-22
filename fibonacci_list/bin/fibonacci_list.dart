import 'package:fibonacci_list/fibonacci.dart';

void main(List<String> arguments) {
  final cantidad = arguments.isEmpty ? 10 : int.tryParse(arguments.first) ?? 10;

  final generador = const FibonacciGenerator();
  final sucesion = generador.generar(cantidad);

  print('Primeros $cantidad números de Fibonacci:');
  print(sucesion.join(', '));
}
