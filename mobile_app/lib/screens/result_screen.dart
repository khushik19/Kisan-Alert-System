import 'dart:io';
import 'package:flutter/material.dart';
import '../services/api_service.dart';

class ResultScreen extends StatefulWidget {
  final File imageFile;
  const ResultScreen({super.key, required this.imageFile});

  @override
  State<ResultScreen> createState() => _ResultScreenState();
}

class _ResultScreenState extends State<ResultScreen> {
  Map<String, dynamic>? _diagnosis;
  Map<String, dynamic>? _advisory;
  String _language = "Hindi";
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _runPipeline();
  }

  Future<void> _runPipeline() async {
    setState(() => _loading = true);
    final diagnosis = await ApiService.diagnose(widget.imageFile);
    final advisory = await ApiService.getAdvisory(diagnosis, _language);
    setState(() {
      _diagnosis = diagnosis;
      _advisory = advisory;
      _loading = false;
    });
  }

  void _toggleLanguage() {
    setState(() => _language = _language == "Hindi" ? "English" : "Hindi");
    _runPipeline();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Diagnosis Result"),
        actions: [
          TextButton(
            onPressed: _toggleLanguage,
            child: Text(_language, style: const TextStyle(color: Colors.white)),
          ),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Image.file(widget.imageFile, height: 200),
                  const SizedBox(height: 16),
                  Text("Diagnosis: ${_diagnosis?['disease']} (${_diagnosis?['confidence']}%)",
                      style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 12),
                  Text("Advisory:", style: const TextStyle(fontWeight: FontWeight.bold)),
                  Text(_advisory?['advisory_text'] ?? "", style: const TextStyle(fontSize: 16)),
                ],
              ),
            ),
    );
  }
}