import 'package:flutter/material.dart';
import 'screens/home_screen.dart';

void main() => runApp(const KisanAlertApp());

class KisanAlertApp extends StatelessWidget {
  const KisanAlertApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Kisan Alert',
      theme: ThemeData(primarySwatch: Colors.green, useMaterial3: true),
      home: const HomeScreen(),
    );
  }
}