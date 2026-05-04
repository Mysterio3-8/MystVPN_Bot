import 'dart';
import 'dart:convert';
import 'dart:typed_data';
import 'package:crypto/crypto.dart';

/// MystVPN Key Bundle format
enum KeyType {
  cpn,
  vless,
  vmess,
  shadowsocks,
  trojan,
}

/// Parsed key configuration
class KeyConfig {
  final KeyType type;
  final Map<String, dynamic> config;
  final String? name;

  KeyConfig({
    required this.type,
    required this.config,
    this.name,
  });
}

/// Universal key parser
class KeyParser {
  /// Parse any supported key format
  static KeyConfig? parse(String input) {
    input = input.trim();

    // MystVPN URI
    if (input.startsWith('mystvpn://')) {
      return _parseMystVpnUri(input);
    }

    // CPN config file
    if (input.startsWith('{') || input.endsWith('.cpn')) {
      return _parseCpnConfig(input);
    }

    // VLESS URI
    if (input.startsWith('vless://')) {
      return _parseVlessUri(input);
    }

    // VMess URI
    if (input.startsWith('vmess://')) {
      return _parseVmessUri(input);
    }

    // Shadowsocks URI
    if (input.startsWith('ss://')) {
      return _parseSsUri(input);
    }

    // Trojan URI
    if (input.startsWith('trojan://')) {
      return _parseTrojanUri(input);
    }

    return null;
  }

  static KeyConfig? _parseMystVpnUri(String input) {
    try {
      final uri = Uri.parse(input);
      final data = uri.queryParameters['data'];
      if (data == null) return null;

      final decoded = utf8.decode(base64Decode(data));
      final json = jsonDecode(decoded) as Map<String, dynamic>;

      return KeyConfig(
        type: KeyType.cpn,
        config: json,
        name: json['name'] as String?,
      );
    } catch (_) {
      return null;
    }
  }

  static KeyConfig? _parseCpnConfig(String input) {
    try {
      final json = jsonDecode(input) as Map<String, dynamic>;

      // Check for CPN-specific fields
      if (json.containsKey('protocol') && json['protocol'] == 'cpn') {
        return KeyConfig(
          type: KeyType.cpn,
          config: json,
          name: json['name'] as String?,
        );
      }

      // XRay/Sing-box format
      if (json.containsKey('outbounds')) {
        return KeyConfig(
          type: KeyType.vless,
          config: json,
          name: json['name'] as String?,
        );
      }

      return null;
    } catch (_) {
      return null;
    }
  }

  static KeyConfig? _parseVlessUri(String input) {
    try {
      final uri = Uri.parse(input.replaceFirst('vless://', 'https://'));
      final config = <String, dynamic>{
        'protocol': 'vless',
        'server': uri.host,
        'port': uri.port,
        'uuid': uri.userInfo,
        'tls': uri.queryParameters['security'] == 'tls',
        'servername': uri.queryParameters['sni'],
      };

      return KeyConfig(type: KeyType.vless, config: config);
    } catch (_) {
      return null;
    }
  }

  static KeyConfig? _parseVmessUri(String input) {
    try {
      final data = input.replaceFirst('vmess://', '');
      final decoded = utf8.decode(base64Decode(data));
      final json = jsonDecode(decoded) as Map<String, dynamic>;

      final config = <String, dynamic>{
        'protocol': 'vmess',
        'server': json['add'],
        'port': json['port'],
        'uuid': json['id'],
        'alterId': json['aid'],
        'tls': json['tls'] == 'tls',
      };

      return KeyConfig(type: KeyType.vmess, config: config);
    } catch (_) {
      return null;
    }
  }

  static KeyConfig? _parseSsUri(String input) {
    try {
      final uri = Uri.parse(input.replaceFirst('ss://', 'https://'));
      final userInfo = utf8.decode(base64Decode(uri.userInfo));
      final parts = userInfo.split(':');

      final config = <String, dynamic>{
        'protocol': 'shadowsocks',
        'server': uri.host,
        'port': uri.port,
        'method': parts[0],
        'password': parts[1],
      };

      return KeyConfig(type: KeyType.shadowsocks, config: config);
    } catch (_) {
      return null;
    }
  }

  static KeyConfig? _parseTrojanUri(String input) {
    try {
      final uri = Uri.parse(input.replaceFirst('trojan://', 'https://'));
      final config = <String, dynamic>{
        'protocol': 'trojan',
        'server': uri.host,
        'port': uri.port,
        'password': uri.userInfo,
        'sni': uri.queryParameters['sni'],
      };

      return KeyConfig(type: KeyType.trojan, config: config);
    } catch (_) {
      return null;
    }
  }
}

/// CPN Key Bundle structure
class CpnKeyBundle {
  final String clientId;
  final String accessToken;
  final String? refreshToken;
  final DateTime expiresAt;
  final List<String> sniList;
  final double keepaliveInterval;
  final JitterProfile jitterProfile;
  final List<TransportType> transportPriority;
  final int paddingShift;

  CpnKeyBundle({
    required this.clientId,
    required this.accessToken,
    this.refreshToken,
    required this.expiresAt,
    required this.sniList,
    required this.keepaliveInterval,
    required this.jitterProfile,
    required this.transportPriority,
    required this.paddingShift,
  });

  factory CpnKeyBundle.fromJson(Map<String, dynamic> json) {
    return CpnKeyBundle(
      clientId: json['client_id'] as String,
      accessToken: json['access_token'] as String,
      refreshToken: json['refresh_token'] as String?,
      expiresAt: DateTime.fromMillisecondsSinceEpoch(
        (json['expires_at'] as int) * 1000,
      ),
      sniList: (json['sni_list'] as List<dynamic>)
          .map((e) => e as String)
          .toList(),
      keepaliveInterval: json['keepalive_interval'] as double,
      jitterProfile: JitterProfile.values.firstWhere(
        (e) => e.name == json['jitter_profile'],
      ),
      transportPriority: (json['transport_priority'] as List<dynamic>)
          .map((e) => TransportType.values.firstWhere((t) => t.name == e))
          .toList(),
      paddingShift: json['padding_shift'] as int,
    );
  }
}

enum JitterProfile { uniform, normal, exponential }

enum TransportType { tls, websocket, quic }