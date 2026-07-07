import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;

class ApiService {
  // Pointing to our live localtunnel backend URL (expose with: npx localtunnel --port 8000)
  static const String baseUrl = "https://great-tiger-9.loca.lt";
  static const bool useMockData = false; // Connected to real backend!

  static Future<Map<String, dynamic>> diagnose(File imageFile) async {
    if (useMockData) {
      await Future.delayed(const Duration(seconds: 1)); // simulate network delay
      return {
        "disease": "Bacterial Blight",
        "confidence": 92,
        "remedy": "Apply copper-based fungicide within 24 hours",
      };
    }

    var request = http.MultipartRequest('POST', Uri.parse('$baseUrl/diagnose'));
    request.files.add(await http.MultipartFile.fromPath('file', imageFile.path));
    var streamedResponse = await request.send();
    var response = await http.Response.fromStream(streamedResponse);
    return jsonDecode(response.body);
  }

  static Future<Map<String, dynamic>> getAdvisory(
      Map<String, dynamic> diagnosis, String language) async {
    if (useMockData) {
      await Future.delayed(const Duration(seconds: 1));
      return {
        "advisory_text": language == "Hindi"
            ? "24 घंटे के भीतर कॉपर-आधारित फफूंदनाशक डालें"
            : "Apply copper-based fungicide within 24 hours",
        "language": language,
      };
    }

    final response = await http.post(
      Uri.parse('$baseUrl/advisory'),
      headers: {"Content-Type": "application/json"},
      body: jsonEncode({"diagnosis": diagnosis, "language": language}),
    );
    return jsonDecode(response.body);
  }
}