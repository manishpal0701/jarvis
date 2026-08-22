// FILE: ek_python_calculator_bana.py

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:ek_python_calculator_prog/ek_python_calculator_prog.dart';

class EkpPythonCalculatorBana {
  final _cubit = Provider.of<EkpPythonCalculatorCubit>(context);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Ek Python Calculator'),
      ),
      body: Center(
        child: EkpPythonCalculatorScreen(),
      ),
    );
  }