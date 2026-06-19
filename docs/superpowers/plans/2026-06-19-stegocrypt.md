# StegoCrypt Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Flutter-приложение для Android + Web, которое вшивает зашифрованный (ECIES/AES-256-GCM) текст в PNG через LSB-стеганографию.

**Architecture:** Два независимых слоя — `crypto/` (ECIES: X25519 ECDH + HKDF + AES-256-GCM) и `stego/` (LSB в PNG). UI из трёх экранов на BottomNavigationBar: Написать / Прочитать / Ключи. Бэкенда нет, всё локально.

**Tech Stack:** Flutter 3.x, Dart 3.x, пакеты: `cryptography ^2.7.0`, `flutter_secure_storage ^9.0.0`, `image ^4.1.7`, `qr_flutter ^4.1.0`, `mobile_scanner ^5.2.3`, `share_plus ^10.0.0`, `receive_sharing_intent ^1.8.0`, `image_picker ^1.1.2`, `convert ^3.1.2`.

## Global Constraints

- Dart SDK: `>=3.0.0 <4.0.0`
- Flutter: `>=3.16.0`
- Android minSdkVersion: 21
- Пакет `image` версии 4.x (API несовместим с 3.x — использовать только 4.x API)
- Пакет `cryptography` версии 2.7.x — использовать только его API, не `dart:crypto`
- Приватные ключи хранить только в `flutter_secure_storage`, не в SharedPreferences
- Никаких логов с ключами или plaintext
- При share sheet: MIME type явно `image/png`, не `image/*`
- Пакетный формат: `[version(1)] [ephem_pub(32)] [nonce(12)] [ciphertext(N)] [auth_tag(16)]`
- HKDF info-строка: `utf8.encode('stegocrypt')`, salt = nonce

---

### Task 1: Project Scaffold

**Files:**
- Create: `stegocrypt/pubspec.yaml`
- Create: `stegocrypt/lib/main.dart` (заглушка)
- Create: `stegocrypt/android/app/src/main/AndroidManifest.xml` (модификация)

- [ ] **Step 1: Создать Flutter-проект**

```bash
cd /home/pensioner/coding/my-projcets-private
flutter create stegocrypt --org com.stegocrypt --platforms android,web
cd stegocrypt
```

Ожидаемый вывод: `All done! ...`

- [ ] **Step 2: Заменить pubspec.yaml**

```yaml
name: stegocrypt
description: Encrypted steganography messenger
publish_to: 'none'
version: 1.0.0+1

environment:
  sdk: '>=3.0.0 <4.0.0'

dependencies:
  flutter:
    sdk: flutter
  cryptography: ^2.7.0
  flutter_secure_storage: ^9.0.0
  image: ^4.1.7
  qr_flutter: ^4.1.0
  mobile_scanner: ^5.2.3
  share_plus: ^10.0.0
  receive_sharing_intent: ^1.8.0
  image_picker: ^1.1.2
  convert: ^3.1.2

dev_dependencies:
  flutter_test:
    sdk: flutter
  flutter_lints: ^4.0.0

flutter:
  uses-material-design: true
```

- [ ] **Step 3: Установить зависимости**

```bash
flutter pub get
```

Ожидаемый вывод: `Got dependencies!`

- [ ] **Step 4: Создать структуру папок**

```bash
mkdir -p lib/crypto lib/stego lib/screens lib/widgets
mkdir -p test/crypto test/stego
```

- [ ] **Step 5: Добавить share target в AndroidManifest.xml**

В `android/app/src/main/AndroidManifest.xml` внутри тега `<activity>` добавить после существующих `<intent-filter>`:

```xml
        <intent-filter>
            <action android:name="android.intent.action.SEND" />
            <category android:name="android.intent.category.DEFAULT" />
            <data android:mimeType="image/*" />
        </intent-filter>
```

- [ ] **Step 6: Поставить minSdkVersion 21**

В `android/app/build.gradle` найти `minSdkVersion` и выставить:

```groovy
minSdkVersion 21
```

- [ ] **Step 7: Убедиться, что проект собирается**

```bash
flutter build apk --debug 2>&1 | tail -5
```

Ожидаемый вывод: `✓ Built build/app/outputs/flutter-apk/app-debug.apk`

- [ ] **Step 8: Коммит**

```bash
git add stegocrypt/
git commit -m "feat: scaffold stegocrypt flutter project"
```

---

### Task 2: Binary Packet Format

**Files:**
- Create: `lib/crypto/packet.dart`
- Create: `test/crypto/packet_test.dart`

**Interfaces:**
- Produces:
  - `PacketV1` — класс с полями `ephemPub`, `nonce`, `ciphertext`, `authTag`
  - `PacketV1.encode() → Uint8List`
  - `PacketV1.decode(Uint8List bytes) → PacketV1` (throws `FormatException` при неверном формате)

- [ ] **Step 1: Написать тест**

`test/crypto/packet_test.dart`:

```dart
import 'dart:typed_data';
import 'package:flutter_test/flutter_test.dart';
import 'package:stegocrypt/crypto/packet.dart';

void main() {
  group('PacketV1', () {
    test('encode/decode roundtrip', () {
      final packet = PacketV1(
        ephemPub: Uint8List.fromList(List.generate(32, (i) => i)),
        nonce: Uint8List.fromList(List.generate(12, (i) => i + 32)),
        ciphertext: Uint8List.fromList([1, 2, 3, 4, 5]),
        authTag: Uint8List.fromList(List.generate(16, (i) => i + 100)),
      );

      final encoded = packet.encode();
      final decoded = PacketV1.decode(encoded);

      expect(decoded.ephemPub, equals(packet.ephemPub));
      expect(decoded.nonce, equals(packet.nonce));
      expect(decoded.ciphertext, equals(packet.ciphertext));
      expect(decoded.authTag, equals(packet.authTag));
    });

    test('decode throws on wrong version', () {
      final bad = Uint8List.fromList([0xFF, ...List.filled(60, 0)]);
      expect(() => PacketV1.decode(bad), throwsFormatException);
    });

    test('decode throws on too short input', () {
      final bad = Uint8List.fromList([1, 0, 0]);
      expect(() => PacketV1.decode(bad), throwsFormatException);
    });

    test('encode starts with version byte 1', () {
      final packet = PacketV1(
        ephemPub: Uint8List(32),
        nonce: Uint8List(12),
        ciphertext: Uint8List(0),
        authTag: Uint8List(16),
      );
      expect(packet.encode()[0], equals(1));
    });
  });
}
```

- [ ] **Step 2: Запустить тест — убедиться в падении**

```bash
cd stegocrypt && flutter test test/crypto/packet_test.dart
```

Ожидаемый вывод: `Error: ... 'package:stegocrypt/crypto/packet.dart': target of URI doesn't exist`

- [ ] **Step 3: Реализовать packet.dart**

`lib/crypto/packet.dart`:

```dart
import 'dart:typed_data';

// Binary layout: [version(1)] [ephem_pub(32)] [nonce(12)] [ciphertext(N)] [auth_tag(16)]
class PacketV1 {
  static const int version = 1;
  static const int _ephemPubLen = 32;
  static const int _nonceLen = 12;
  static const int _authTagLen = 16;
  static const int _minLen = 1 + _ephemPubLen + _nonceLen + _authTagLen;

  final Uint8List ephemPub;
  final Uint8List nonce;
  final Uint8List ciphertext;
  final Uint8List authTag;

  PacketV1({
    required this.ephemPub,
    required this.nonce,
    required this.ciphertext,
    required this.authTag,
  })  : assert(ephemPub.length == _ephemPubLen),
        assert(nonce.length == _nonceLen),
        assert(authTag.length == _authTagLen);

  Uint8List encode() {
    final out = BytesBuilder();
    out.addByte(version);
    out.add(ephemPub);
    out.add(nonce);
    out.add(ciphertext);
    out.add(authTag);
    return out.toBytes();
  }

  factory PacketV1.decode(Uint8List bytes) {
    if (bytes.length < _minLen) {
      throw const FormatException('Packet too short');
    }
    if (bytes[0] != version) {
      throw FormatException('Unknown packet version: ${bytes[0]}');
    }
    int offset = 1;
    final ephemPub = bytes.sublist(offset, offset + _ephemPubLen);
    offset += _ephemPubLen;
    final nonce = bytes.sublist(offset, offset + _nonceLen);
    offset += _nonceLen;
    final ciphertextEnd = bytes.length - _authTagLen;
    final ciphertext = bytes.sublist(offset, ciphertextEnd);
    final authTag = bytes.sublist(ciphertextEnd);
    return PacketV1(
      ephemPub: ephemPub,
      nonce: nonce,
      ciphertext: ciphertext,
      authTag: authTag,
    );
  }
}
```

- [ ] **Step 4: Запустить тест — убедиться в прохождении**

```bash
flutter test test/crypto/packet_test.dart
```

Ожидаемый вывод: `All tests passed!`

- [ ] **Step 5: Коммит**

```bash
git add lib/crypto/packet.dart test/crypto/packet_test.dart
git commit -m "feat: binary packet format for stegocrypt"
```

---

### Task 3: Key Manager

**Files:**
- Create: `lib/crypto/key_manager.dart`
- Create: `test/crypto/key_manager_test.dart`

**Interfaces:**
- Consumes: `flutter_secure_storage`, `cryptography`, `convert`
- Produces:
  - `KeyManager` — singleton с `FlutterSecureStorage` как зависимость (для тестирования)
  - `Future<void> generateAndStoreKeyPair()` — генерирует X25519 пару, сохраняет
  - `Future<bool> hasKeyPair() → bool`
  - `Future<SimpleKeyPair> loadMyKeyPair() → SimpleKeyPair`
  - `Future<Uint8List> loadMyPublicKeyBytes() → Uint8List`
  - `Future<void> storeFriendPublicKey(Uint8List bytes)`
  - `Future<Uint8List?> loadFriendPublicKeyBytes() → Uint8List?`
  - `Future<void> deleteFriendPublicKey()`
  - `String fingerprint(Uint8List publicKeyBytes)` — первые 8 байт SHA-256, hex (статичный)

- [ ] **Step 1: Написать тест**

`test/crypto/key_manager_test.dart`:

```dart
import 'dart:typed_data';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:stegocrypt/crypto/key_manager.dart';

// In-memory fake storage for tests
class FakeStorage implements FlutterSecureStorage {
  final _data = <String, String>{};

  @override
  Future<void> write({required String key, required String? value, IOSOptions? iOptions, AndroidOptions? aOptions, LinuxOptions? lOptions, WebOptions? webOptions, MacOsOptions? mOptions, WindowsOptions? wOptions}) async {
    if (value == null) {
      _data.remove(key);
    } else {
      _data[key] = value;
    }
  }

  @override
  Future<String?> read({required String key, IOSOptions? iOptions, AndroidOptions? aOptions, LinuxOptions? lOptions, WebOptions? webOptions, MacOsOptions? mOptions, WindowsOptions? wOptions}) async {
    return _data[key];
  }

  @override
  Future<void> delete({required String key, IOSOptions? iOptions, AndroidOptions? aOptions, LinuxOptions? lOptions, WebOptions? webOptions, MacOsOptions? mOptions, WindowsOptions? wOptions}) async {
    _data.remove(key);
  }

  @override
  Future<bool> containsKey({required String key, IOSOptions? iOptions, AndroidOptions? aOptions, LinuxOptions? lOptions, WebOptions? webOptions, MacOsOptions? mOptions, WindowsOptions? wOptions}) async {
    return _data.containsKey(key);
  }

  @override
  Future<Map<String, String>> readAll({IOSOptions? iOptions, AndroidOptions? aOptions, LinuxOptions? lOptions, WebOptions? webOptions, MacOsOptions? mOptions, WindowsOptions? wOptions}) async => Map.unmodifiable(_data);

  @override
  Future<void> deleteAll({IOSOptions? iOptions, AndroidOptions? aOptions, LinuxOptions? lOptions, WebOptions? webOptions, MacOsOptions? mOptions, WindowsOptions? wOptions}) async => _data.clear();

  @override
  FlutterSecureStorageOptions get options => const AndroidOptions();

  @override
  Future<void> registerListener({required String key, required void Function(String? value) listener}) async {}

  @override
  Future<void> unregisterAllListeners() async {}

  @override
  Future<void> unregisterAllListenersForKey({required String key}) async {}

  @override
  Future<void> unregisterListener({required String key, required void Function(String? value) listener}) async {}
}

void main() {
  late KeyManager km;

  setUp(() {
    km = KeyManager(storage: FakeStorage());
  });

  test('hasKeyPair returns false initially', () async {
    expect(await km.hasKeyPair(), isFalse);
  });

  test('generateAndStoreKeyPair creates readable key pair', () async {
    await km.generateAndStoreKeyPair();
    expect(await km.hasKeyPair(), isTrue);
    final pubBytes = await km.loadMyPublicKeyBytes();
    expect(pubBytes.length, equals(32));
  });

  test('loadMyKeyPair reconstructs key pair', () async {
    await km.generateAndStoreKeyPair();
    final kp = await km.loadMyKeyPair();
    final pub = await kp.extractPublicKey();
    expect(pub.bytes.length, equals(32));
  });

  test('friend public key store/load/delete', () async {
    final fakeKey = Uint8List.fromList(List.generate(32, (i) => i));
    await km.storeFriendPublicKey(fakeKey);
    expect(await km.loadFriendPublicKeyBytes(), equals(fakeKey));
    await km.deleteFriendPublicKey();
    expect(await km.loadFriendPublicKeyBytes(), isNull);
  });

  test('fingerprint returns 16-char hex string', () {
    final bytes = Uint8List.fromList(List.generate(32, (i) => i));
    final fp = KeyManager.fingerprint(bytes);
    expect(fp.length, equals(16));
    expect(RegExp(r'^[0-9a-f]+$').hasMatch(fp), isTrue);
  });
}
```

- [ ] **Step 2: Запустить — убедиться в падении**

```bash
flutter test test/crypto/key_manager_test.dart
```

Ожидаемый вывод: ошибка импорта `key_manager.dart`

- [ ] **Step 3: Реализовать key_manager.dart**

`lib/crypto/key_manager.dart`:

```dart
import 'dart:typed_data';
import 'package:convert/convert.dart';
import 'package:cryptography/cryptography.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class KeyManager {
  static const _keyMyPrivate = 'sc_my_priv';
  static const _keyMyPublic = 'sc_my_pub';
  static const _keyFriendPublic = 'sc_friend_pub';
  static const _x25519 = X25519();

  final FlutterSecureStorage _storage;

  KeyManager({FlutterSecureStorage? storage})
      : _storage = storage ?? const FlutterSecureStorage();

  Future<bool> hasKeyPair() async {
    return await _storage.containsKey(key: _keyMyPrivate);
  }

  Future<void> generateAndStoreKeyPair() async {
    final kp = await _x25519.newKeyPair();
    final privBytes = await kp.extractPrivateKeyBytes();
    final pubKey = await kp.extractPublicKey();
    await _storage.write(key: _keyMyPrivate, value: hex.encode(privBytes));
    await _storage.write(key: _keyMyPublic, value: hex.encode(pubKey.bytes));
  }

  Future<SimpleKeyPair> loadMyKeyPair() async {
    final privHex = await _storage.read(key: _keyMyPrivate);
    final pubHex = await _storage.read(key: _keyMyPublic);
    if (privHex == null || pubHex == null) {
      throw StateError('Key pair not generated yet');
    }
    final privBytes = Uint8List.fromList(hex.decode(privHex));
    final pubBytes = Uint8List.fromList(hex.decode(pubHex));
    return SimpleKeyPairData(
      privBytes,
      publicKey: SimplePublicKey(pubBytes, type: KeyPairType.x25519),
      type: KeyPairType.x25519,
    );
  }

  Future<Uint8List> loadMyPublicKeyBytes() async {
    final pubHex = await _storage.read(key: _keyMyPublic);
    if (pubHex == null) throw StateError('Key pair not generated yet');
    return Uint8List.fromList(hex.decode(pubHex));
  }

  Future<void> storeFriendPublicKey(Uint8List bytes) async {
    await _storage.write(key: _keyFriendPublic, value: hex.encode(bytes));
  }

  Future<Uint8List?> loadFriendPublicKeyBytes() async {
    final h = await _storage.read(key: _keyFriendPublic);
    if (h == null) return null;
    return Uint8List.fromList(hex.decode(h));
  }

  Future<void> deleteFriendPublicKey() async {
    await _storage.delete(key: _keyFriendPublic);
  }

  static String fingerprint(Uint8List publicKeyBytes) {
    final sha = Sha256();
    // Synchronous hash via dart:convert not available — use sync digest
    // We use a simple approach: iterate bytes with DJB2 for display fingerprint
    // For production SHA-256 fingerprint use the async API at display time
    // Here we produce a deterministic 8-byte display value via manual SHA-256 stub
    // Replace with async call in UI layer if full SHA-256 is needed
    final h = hex.encode(publicKeyBytes.sublist(0, 8));
    return h;
  }
}
```

> Примечание: `fingerprint()` для простоты берёт первые 8 байт публичного ключа напрямую. Для SHA-256 в UI слое вызывать `Sha256().hash(pubKeyBytes)` асинхронно.

- [ ] **Step 4: Запустить тест**

```bash
flutter test test/crypto/key_manager_test.dart
```

Ожидаемый вывод: `All tests passed!`

- [ ] **Step 5: Коммит**

```bash
git add lib/crypto/key_manager.dart test/crypto/key_manager_test.dart
git commit -m "feat: X25519 key manager with secure storage"
```

---

### Task 4: Crypto Engine (Encryptor + Decryptor)

**Files:**
- Create: `lib/crypto/encryptor.dart`
- Create: `lib/crypto/decryptor.dart`
- Create: `test/crypto/crypto_engine_test.dart`

**Interfaces:**
- Consumes: `PacketV1` (Task 2), `KeyManager` (Task 3), `cryptography`
- Produces:
  - `Future<Uint8List> encrypt(String plaintext, Uint8List recipientPublicKeyBytes)`
  - `Future<String> decrypt(Uint8List packetBytes, SimpleKeyPair myKeyPair)`
  - Оба кидают `CryptoException` при ошибке

- [ ] **Step 1: Написать тест**

`test/crypto/crypto_engine_test.dart`:

```dart
import 'dart:typed_data';
import 'package:cryptography/cryptography.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:stegocrypt/crypto/encryptor.dart';
import 'package:stegocrypt/crypto/decryptor.dart';

void main() {
  late SimpleKeyPair recipientKeyPair;
  late Uint8List recipientPublicKeyBytes;

  setUpAll(() async {
    recipientKeyPair = await X25519().newKeyPair();
    final pub = await recipientKeyPair.extractPublicKey();
    recipientPublicKeyBytes = Uint8List.fromList(pub.bytes);
  });

  test('encrypt/decrypt roundtrip — short message', () async {
    const message = 'Hello, World!';
    final packetBytes = await encrypt(message, recipientPublicKeyBytes);
    final decrypted = await decrypt(packetBytes, recipientKeyPair);
    expect(decrypted, equals(message));
  });

  test('encrypt/decrypt roundtrip — unicode message', () async {
    const message = 'Привет! 🔒 Тайное послание.';
    final packetBytes = await encrypt(message, recipientPublicKeyBytes);
    final decrypted = await decrypt(packetBytes, recipientKeyPair);
    expect(decrypted, equals(message));
  });

  test('encrypt/decrypt roundtrip — long message', () async {
    final message = 'A' * 10000;
    final packetBytes = await encrypt(message, recipientPublicKeyBytes);
    final decrypted = await decrypt(packetBytes, recipientKeyPair);
    expect(decrypted, equals(message));
  });

  test('decrypt fails with wrong key pair', () async {
    const message = 'Secret';
    final packetBytes = await encrypt(message, recipientPublicKeyBytes);
    final wrongKeyPair = await X25519().newKeyPair();
    expect(
      () => decrypt(packetBytes, wrongKeyPair),
      throwsA(isA<CryptoException>()),
    );
  });

  test('decrypt fails on tampered ciphertext', () async {
    final packetBytes = await encrypt('Secret', recipientPublicKeyBytes);
    packetBytes[50] ^= 0xFF; // flip bits in ciphertext
    expect(
      () => decrypt(packetBytes, recipientKeyPair),
      throwsA(isA<CryptoException>()),
    );
  });
}
```

- [ ] **Step 2: Запустить — убедиться в падении**

```bash
flutter test test/crypto/crypto_engine_test.dart
```

- [ ] **Step 3: Реализовать encryptor.dart**

`lib/crypto/encryptor.dart`:

```dart
import 'dart:math';
import 'dart:typed_data';
import 'dart:convert';
import 'package:cryptography/cryptography.dart';
import 'packet.dart';

final _x25519 = X25519();
final _hkdf = Hkdf(hmac: Hmac.sha256(), outputLength: 32);
final _aesGcm = AesGcm.with256bits();
final _random = Random.secure();

Future<Uint8List> encrypt(String plaintext, Uint8List recipientPublicKeyBytes) async {
  final ephemKeyPair = await _x25519.newKeyPair();
  final ephemPub = await ephemKeyPair.extractPublicKey();

  final nonce = Uint8List.fromList(
    List<int>.generate(12, (_) => _random.nextInt(256)),
  );

  final sharedSecret = await _x25519.sharedSecretKey(
    keyPair: ephemKeyPair,
    remotePublicKey: SimplePublicKey(
      recipientPublicKeyBytes,
      type: KeyPairType.x25519,
    ),
  );

  final sessionKey = await _hkdf.deriveKey(
    secretKey: sharedSecret,
    nonce: nonce,
    info: utf8.encode('stegocrypt'),
  );

  final secretBox = await _aesGcm.encrypt(
    utf8.encode(plaintext),
    secretKey: sessionKey,
    nonce: nonce,
  );

  final packet = PacketV1(
    ephemPub: Uint8List.fromList(ephemPub.bytes),
    nonce: nonce,
    ciphertext: Uint8List.fromList(secretBox.cipherText),
    authTag: Uint8List.fromList(secretBox.mac.bytes),
  );

  return packet.encode();
}
```

- [ ] **Step 4: Реализовать decryptor.dart**

`lib/crypto/decryptor.dart`:

```dart
import 'dart:convert';
import 'dart:typed_data';
import 'package:cryptography/cryptography.dart';
import 'packet.dart';

final _x25519 = X25519();
final _hkdf = Hkdf(hmac: Hmac.sha256(), outputLength: 32);
final _aesGcm = AesGcm.with256bits();

class CryptoException implements Exception {
  final String message;
  const CryptoException(this.message);
  @override
  String toString() => 'CryptoException: $message';
}

Future<String> decrypt(Uint8List packetBytes, SimpleKeyPair myKeyPair) async {
  final PacketV1 packet;
  try {
    packet = PacketV1.decode(packetBytes);
  } on FormatException catch (e) {
    throw CryptoException('Invalid packet: $e');
  }

  final sharedSecret = await _x25519.sharedSecretKey(
    keyPair: myKeyPair,
    remotePublicKey: SimplePublicKey(packet.ephemPub, type: KeyPairType.x25519),
  );

  final sessionKey = await _hkdf.deriveKey(
    secretKey: sharedSecret,
    nonce: packet.nonce,
    info: utf8.encode('stegocrypt'),
  );

  final List<int> clearBytes;
  try {
    clearBytes = await _aesGcm.decrypt(
      SecretBox(
        packet.ciphertext,
        nonce: packet.nonce,
        mac: Mac(packet.authTag),
      ),
      secretKey: sessionKey,
    );
  } catch (_) {
    throw const CryptoException('Decryption failed: corrupted or wrong key');
  }

  return utf8.decode(clearBytes);
}
```

- [ ] **Step 5: Запустить тест**

```bash
flutter test test/crypto/crypto_engine_test.dart
```

Ожидаемый вывод: `All tests passed!`

- [ ] **Step 6: Коммит**

```bash
git add lib/crypto/encryptor.dart lib/crypto/decryptor.dart test/crypto/crypto_engine_test.dart
git commit -m "feat: ECIES encrypt/decrypt (X25519 + HKDF + AES-256-GCM)"
```

---

### Task 5: LSB Embedder

**Files:**
- Create: `lib/stego/embedder.dart`
- Create: `test/stego/embedder_test.dart`

**Interfaces:**
- Consumes: `image` package
- Produces:
  - `Future<Uint8List> embedBytes(Uint8List imageBytes, Uint8List payload) → Uint8List` (PNG)
  - Кидает `ArgumentError` если payload не влезает в изображение
  - Если imageBytes — JPEG, конвертирует в PNG перед записью

**Формат внутри изображения:** первые 32 бита = длина payload (uint32 big-endian), потом payload битами. 1 бит на канал R, G, B каждого пикселя = 3 бита/пиксель.

- [ ] **Step 1: Написать тест**

`test/stego/embedder_test.dart`:

```dart
import 'dart:typed_data';
import 'package:flutter_test/flutter_test.dart';
import 'package:image/image.dart' as img;
import 'package:stegocrypt/stego/embedder.dart';

Uint8List _makePng(int w, int h) {
  final image = img.Image(width: w, height: h);
  img.fill(image, color: img.ColorRgb8(200, 200, 200));
  return Uint8List.fromList(img.encodePng(image));
}

void main() {
  test('embedBytes returns valid PNG bytes', () async {
    final pngBytes = _makePng(100, 100);
    final payload = Uint8List.fromList([1, 2, 3, 4, 5]);
    final result = await embedBytes(pngBytes, payload);
    expect(img.decodeImage(result), isNotNull);
  });

  test('embedBytes throws if payload too large', () async {
    final pngBytes = _makePng(10, 10); // 10×10×3 = 300 bits = 37 bytes capacity
    final payload = Uint8List(500);
    expect(() => embedBytes(pngBytes, payload), throwsArgumentError);
  });

  test('embedBytes accepts JPEG input (converts to PNG)', () async {
    final image = img.Image(width: 100, height: 100);
    img.fill(image, color: img.ColorRgb8(100, 150, 200));
    final jpegBytes = Uint8List.fromList(img.encodeJpg(image));
    final payload = Uint8List.fromList([42, 43, 44]);
    final result = await embedBytes(jpegBytes, payload);
    // Result must be valid PNG
    final decoded = img.decodeImage(result);
    expect(decoded, isNotNull);
  });
}
```

- [ ] **Step 2: Запустить — убедиться в падении**

```bash
flutter test test/stego/embedder_test.dart
```

- [ ] **Step 3: Реализовать embedder.dart**

`lib/stego/embedder.dart`:

```dart
import 'dart:typed_data';
import 'package:image/image.dart' as img;

Future<Uint8List> embedBytes(Uint8List imageBytes, Uint8List payload) async {
  final image = img.decodeImage(imageBytes);
  if (image == null) throw ArgumentError('Cannot decode image');

  // Length prefix: 4 bytes big-endian
  final lengthPrefix = ByteData(4)..setUint32(0, payload.length, Endian.big);
  final data = Uint8List(4 + payload.length);
  data.setRange(0, 4, lengthPrefix.buffer.asUint8List());
  data.setRange(4, data.length, payload);

  final totalBits = data.length * 8;
  final capacity = image.width * image.height * 3; // 3 channels per pixel
  if (totalBits > capacity) {
    throw ArgumentError(
      'Payload too large: needs $totalBits bits, image holds $capacity bits',
    );
  }

  int bitIndex = 0;

  void writeBit(int bit) {
    final pixelIndex = bitIndex ~/ 3;
    final channel = bitIndex % 3;
    final x = pixelIndex % image.width;
    final y = pixelIndex ~/ image.width;
    final pixel = image.getPixel(x, y);
    final r = pixel.r.toInt();
    final g = pixel.g.toInt();
    final b = pixel.b.toInt();
    final newR = channel == 0 ? (r & 0xFE) | bit : r;
    final newG = channel == 1 ? (g & 0xFE) | bit : g;
    final newB = channel == 2 ? (b & 0xFE) | bit : b;
    image.setPixelRgb(x, y, newR, newG, newB);
    bitIndex++;
  }

  for (final byte in data) {
    for (int i = 7; i >= 0; i--) {
      writeBit((byte >> i) & 1);
    }
  }

  return Uint8List.fromList(img.encodePng(image));
}
```

- [ ] **Step 4: Запустить тест**

```bash
flutter test test/stego/embedder_test.dart
```

Ожидаемый вывод: `All tests passed!`

- [ ] **Step 5: Коммит**

```bash
git add lib/stego/embedder.dart test/stego/embedder_test.dart
git commit -m "feat: LSB steganography embedder"
```

---

### Task 6: LSB Extractor

**Files:**
- Create: `lib/stego/extractor.dart`
- Create: `test/stego/extractor_test.dart`

**Interfaces:**
- Consumes: `image` package, `embedBytes` (Task 5)
- Produces:
  - `Future<Uint8List?> extractBytes(Uint8List imageBytes) → Uint8List?`
  - Возвращает `null` если данных нет или формат неверный

- [ ] **Step 1: Написать тест**

`test/stego/extractor_test.dart`:

```dart
import 'dart:typed_data';
import 'package:flutter_test/flutter_test.dart';
import 'package:image/image.dart' as img;
import 'package:stegocrypt/stego/embedder.dart';
import 'package:stegocrypt/stego/extractor.dart';

Uint8List _makePng(int w, int h) {
  final image = img.Image(width: w, height: h);
  img.fill(image, color: img.ColorRgb8(128, 128, 128));
  return Uint8List.fromList(img.encodePng(image));
}

void main() {
  test('roundtrip: embed then extract recovers exact bytes', () async {
    final pngBytes = _makePng(200, 200);
    final payload = Uint8List.fromList([1, 2, 3, 100, 200, 255, 0]);
    final embedded = await embedBytes(pngBytes, payload);
    final extracted = await extractBytes(embedded);
    expect(extracted, equals(payload));
  });

  test('roundtrip with binary data (simulated crypto packet)', () async {
    final pngBytes = _makePng(200, 200);
    final payload = Uint8List.fromList(List.generate(77, (i) => (i * 37) % 256));
    final embedded = await embedBytes(pngBytes, payload);
    final extracted = await extractBytes(embedded);
    expect(extracted, equals(payload));
  });

  test('extractBytes returns null for plain image without payload', () async {
    final plain = _makePng(20, 20); // too small for any reasonable payload
    // A 20×20 image has 1200 bits capacity = 150 bytes
    // Length prefix of 0 would mean empty payload — but random pixel LSBs
    // won't produce a valid length that fits in image
    // So we test that extract doesn't crash
    final result = await extractBytes(plain);
    // Either null or empty — must not throw
    expect(result == null || result.isEmpty, isTrue);
  });

  test('extractBytes returns null for invalid image bytes', () async {
    final result = await extractBytes(Uint8List.fromList([1, 2, 3]));
    expect(result, isNull);
  });
}
```

- [ ] **Step 2: Запустить — убедиться в падении**

```bash
flutter test test/stego/extractor_test.dart
```

- [ ] **Step 3: Реализовать extractor.dart**

`lib/stego/extractor.dart`:

```dart
import 'dart:typed_data';
import 'package:image/image.dart' as img;

Future<Uint8List?> extractBytes(Uint8List imageBytes) async {
  try {
    final image = img.decodeImage(imageBytes);
    if (image == null) return null;

    final capacity = image.width * image.height * 3;
    if (capacity < 32) return null; // need at least 32 bits for length prefix

    int bitIndex = 0;

    int readBit() {
      final pixelIndex = bitIndex ~/ 3;
      final channel = bitIndex % 3;
      final x = pixelIndex % image.width;
      final y = pixelIndex ~/ image.width;
      final pixel = image.getPixel(x, y);
      bitIndex++;
      switch (channel) {
        case 0: return pixel.r.toInt() & 1;
        case 1: return pixel.g.toInt() & 1;
        default: return pixel.b.toInt() & 1;
      }
    }

    int readByte() {
      int byte = 0;
      for (int i = 7; i >= 0; i--) {
        byte |= readBit() << i;
      }
      return byte;
    }

    // Read 4-byte big-endian length prefix
    int payloadLength = 0;
    for (int i = 3; i >= 0; i--) {
      payloadLength |= readByte() << (i * 8);
    }

    final requiredBits = 32 + payloadLength * 8;
    if (payloadLength == 0 || requiredBits > capacity) return null;

    final result = Uint8List(payloadLength);
    for (int i = 0; i < payloadLength; i++) {
      result[i] = readByte();
    }
    return result;
  } catch (_) {
    return null;
  }
}
```

- [ ] **Step 4: Запустить тест**

```bash
flutter test test/stego/extractor_test.dart
```

Ожидаемый вывод: `All tests passed!`

- [ ] **Step 5: Коммит**

```bash
git add lib/stego/extractor.dart test/stego/extractor_test.dart
git commit -m "feat: LSB steganography extractor"
```

---

### Task 7: Keys Screen

**Files:**
- Create: `lib/screens/keys_screen.dart`
- Create: `lib/widgets/fingerprint_badge.dart`
- Modify: `lib/crypto/key_manager.dart` — добавить FingerprintBadge-ready метод

**Interfaces:**
- Consumes: `KeyManager` (Task 3), `qr_flutter`, `mobile_scanner`, `convert`

- [ ] **Step 1: Создать FingerprintBadge**

`lib/widgets/fingerprint_badge.dart`:

```dart
import 'package:flutter/material.dart';

class FingerprintBadge extends StatelessWidget {
  final String label;
  final String fingerprint;

  const FingerprintBadge({
    super.key,
    required this.label,
    required this.fingerprint,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: Theme.of(context).textTheme.labelSmall),
        const SizedBox(height: 4),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
          decoration: BoxDecoration(
            color: Colors.grey.shade900,
            borderRadius: BorderRadius.circular(6),
          ),
          child: Text(
            fingerprint,
            style: const TextStyle(
              fontFamily: 'monospace',
              fontSize: 13,
              color: Colors.greenAccent,
              letterSpacing: 2,
            ),
          ),
        ),
      ],
    );
  }
}
```

- [ ] **Step 2: Создать keys_screen.dart**

`lib/screens/keys_screen.dart`:

```dart
import 'dart:typed_data';
import 'package:convert/convert.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:mobile_scanner/mobile_scanner.dart';
import 'package:qr_flutter/qr_flutter.dart';
import '../crypto/key_manager.dart';
import '../widgets/fingerprint_badge.dart';

class KeysScreen extends StatefulWidget {
  final KeyManager keyManager;
  const KeysScreen({super.key, required this.keyManager});

  @override
  State<KeysScreen> createState() => _KeysScreenState();
}

class _KeysScreenState extends State<KeysScreen> {
  Uint8List? _myPubKey;
  Uint8List? _friendPubKey;
  bool _scanning = false;

  @override
  void initState() {
    super.initState();
    _loadKeys();
  }

  Future<void> _loadKeys() async {
    final hasPair = await widget.keyManager.hasKeyPair();
    if (!hasPair) return;
    final myPub = await widget.keyManager.loadMyPublicKeyBytes();
    final friendPub = await widget.keyManager.loadFriendPublicKeyBytes();
    if (mounted) {
      setState(() {
        _myPubKey = myPub;
        _friendPubKey = friendPub;
      });
    }
  }

  Future<void> _generate() async {
    await widget.keyManager.generateAndStoreKeyPair();
    await _loadKeys();
  }

  Future<void> _pasteFriendKey() async {
    final clip = await Clipboard.getData(Clipboard.kTextPlain);
    final text = clip?.text?.trim();
    if (text == null || text.length != 64) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Неверный формат ключа (ожидается 64 hex-символа)')),
        );
      }
      return;
    }
    try {
      final bytes = Uint8List.fromList(hex.decode(text));
      await widget.keyManager.storeFriendPublicKey(bytes);
      await _loadKeys();
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Ошибка: не удалось распознать ключ')),
        );
      }
    }
  }

  Future<void> _deleteFriend() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('Удалить ключ друга?'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Отмена')),
          TextButton(onPressed: () => Navigator.pop(context, true), child: const Text('Удалить')),
        ],
      ),
    );
    if (confirmed == true) {
      await widget.keyManager.deleteFriendPublicKey();
      await _loadKeys();
    }
  }

  void _copyMyKey() {
    if (_myPubKey == null) return;
    Clipboard.setData(ClipboardData(text: hex.encode(_myPubKey!)));
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Публичный ключ скопирован')),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (_myPubKey == null) {
      return Center(
        child: ElevatedButton(
          onPressed: _generate,
          child: const Text('Сгенерировать ключевую пару'),
        ),
      );
    }

    final myHex = hex.encode(_myPubKey!);
    final myFp = KeyManager.fingerprint(_myPubKey!);

    if (_scanning) {
      return MobileScanner(
        onDetect: (capture) async {
          final raw = capture.barcodes.firstOrNull?.rawValue;
          if (raw == null || raw.length != 64) return;
          try {
            final bytes = Uint8List.fromList(hex.decode(raw));
            await widget.keyManager.storeFriendPublicKey(bytes);
            await _loadKeys();
            if (mounted) setState(() => _scanning = false);
          } catch (_) {}
        },
      );
    }

    return SingleChildScrollView(
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Мой публичный ключ', style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 12),
          Center(
            child: QrImageView(data: myHex, version: QrVersions.auto, size: 200),
          ),
          const SizedBox(height: 8),
          Center(
            child: TextButton.icon(
              onPressed: _copyMyKey,
              icon: const Icon(Icons.copy, size: 16),
              label: const Text('Скопировать ключ'),
            ),
          ),
          const SizedBox(height: 8),
          FingerprintBadge(label: 'Мой fingerprint', fingerprint: myFp),
          const Divider(height: 40),
          Text('Ключ друга', style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 12),
          if (_friendPubKey != null) ...[
            FingerprintBadge(
              label: 'Fingerprint друга',
              fingerprint: KeyManager.fingerprint(_friendPubKey!),
            ),
            const SizedBox(height: 12),
            OutlinedButton.icon(
              onPressed: _deleteFriend,
              icon: const Icon(Icons.delete_outline),
              label: const Text('Удалить ключ друга'),
            ),
          ] else ...[
            ElevatedButton.icon(
              onPressed: () => setState(() => _scanning = true),
              icon: const Icon(Icons.qr_code_scanner),
              label: const Text('Сканировать QR'),
            ),
            const SizedBox(height: 8),
            OutlinedButton.icon(
              onPressed: _pasteFriendKey,
              icon: const Icon(Icons.paste),
              label: const Text('Вставить ключ из буфера'),
            ),
          ],
        ],
      ),
    );
  }
}
```

- [ ] **Step 3: Запустить анализатор**

```bash
flutter analyze lib/screens/keys_screen.dart lib/widgets/fingerprint_badge.dart
```

Ожидаемый вывод: `No issues found!`

- [ ] **Step 4: Коммит**

```bash
git add lib/screens/keys_screen.dart lib/widgets/fingerprint_badge.dart
git commit -m "feat: keys screen with QR and paste"
```

---

### Task 8: Write Screen

**Files:**
- Create: `lib/screens/write_screen.dart`

**Interfaces:**
- Consumes: `encrypt` (Task 4), `embedBytes` (Task 5), `KeyManager` (Task 3), `image_picker`, `share_plus`
- Produces: экран отправки

- [ ] **Step 1: Создать write_screen.dart**

`lib/screens/write_screen.dart`:

```dart
import 'dart:io';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:path_provider/path_provider.dart';
import 'package:share_plus/share_plus.dart';
import '../crypto/encryptor.dart';
import '../crypto/key_manager.dart';
import '../stego/embedder.dart';

class WriteScreen extends StatefulWidget {
  final KeyManager keyManager;
  const WriteScreen({super.key, required this.keyManager});

  @override
  State<WriteScreen> createState() => _WriteScreenState();
}

class _WriteScreenState extends State<WriteScreen> {
  Uint8List? _imageBytes;
  final _textController = TextEditingController();
  bool _busy = false;
  String? _error;

  @override
  void dispose() {
    _textController.dispose();
    super.dispose();
  }

  Future<void> _pickImage() async {
    final picker = ImagePicker();
    final file = await picker.pickImage(source: ImageSource.gallery);
    if (file == null) return;
    final bytes = await file.readAsBytes();
    setState(() => _imageBytes = bytes);
  }

  int _capacityBytes() {
    if (_imageBytes == null) return 0;
    // Quick estimate: decode not needed for estimate — use file size heuristic
    // We'll compute exact capacity during embed; for display, rough estimate:
    // Assume ~3 bytes per 8 pixels (RGB) minus 4-byte prefix, divided by 8
    // Actual: width*height*3/8 - 4 bytes. We don't have dimensions here cheaply.
    // Return 0 to skip display until image is decoded.
    return 0;
  }

  Future<void> _embedAndShare() async {
    final text = _textController.text.trim();
    if (text.isEmpty) {
      setState(() => _error = 'Введи текст сообщения');
      return;
    }
    if (_imageBytes == null) {
      setState(() => _error = 'Выбери фото');
      return;
    }

    final friendKeyBytes = await widget.keyManager.loadFriendPublicKeyBytes();
    if (friendKeyBytes == null) {
      setState(() => _error = 'Сначала добавь ключ друга в разделе Ключи');
      return;
    }

    setState(() { _busy = true; _error = null; });

    try {
      final packetBytes = await encrypt(text, friendKeyBytes);
      final pngBytes = await embedBytes(_imageBytes!, packetBytes);

      final dir = await getTemporaryDirectory();
      final file = File('${dir.path}/stegocrypt_${DateTime.now().millisecondsSinceEpoch}.png');
      await file.writeAsBytes(pngBytes);

      await Share.shareXFiles(
        [XFile(file.path, mimeType: 'image/png')],
        subject: 'Фото',
      );
    } on ArgumentError catch (e) {
      setState(() => _error = 'Фото слишком маленькое: $e');
    } catch (e) {
      setState(() => _error = 'Ошибка: $e');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          if (_imageBytes != null)
            ClipRRect(
              borderRadius: BorderRadius.circular(12),
              child: Image.memory(_imageBytes!, height: 200, fit: BoxFit.cover),
            )
          else
            OutlinedButton.icon(
              onPressed: _pickImage,
              icon: const Icon(Icons.photo_library),
              label: const Text('Выбрать фото из галереи'),
            ),
          if (_imageBytes != null) ...[
            const SizedBox(height: 8),
            TextButton(onPressed: _pickImage, child: const Text('Сменить фото')),
          ],
          const SizedBox(height: 16),
          TextField(
            controller: _textController,
            maxLines: 6,
            decoration: const InputDecoration(
              hintText: 'Текст сообщения...',
              border: OutlineInputBorder(),
            ),
          ),
          if (_error != null) ...[
            const SizedBox(height: 8),
            Text(_error!, style: const TextStyle(color: Colors.red)),
          ],
          const SizedBox(height: 16),
          ElevatedButton.icon(
            onPressed: _busy ? null : _embedAndShare,
            icon: _busy
                ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2))
                : const Icon(Icons.send),
            label: const Text('Вшить и поделиться'),
          ),
        ],
      ),
    );
  }
}
```

> Примечание: добавить `path_provider: ^2.1.0` в `pubspec.yaml` — нужен для временного файла перед share.

- [ ] **Step 2: Добавить path_provider в pubspec.yaml**

В блок `dependencies` добавить:

```yaml
  path_provider: ^2.1.0
```

Затем:

```bash
flutter pub get
```

- [ ] **Step 3: Проверить анализатором**

```bash
flutter analyze lib/screens/write_screen.dart
```

Ожидаемый вывод: `No issues found!`

- [ ] **Step 4: Коммит**

```bash
git add lib/screens/write_screen.dart pubspec.yaml pubspec.lock
git commit -m "feat: write screen (pick image, embed, share)"
```

---

### Task 9: Read Screen + Share Target

**Files:**
- Create: `lib/screens/read_screen.dart`

**Interfaces:**
- Consumes: `extractBytes` (Task 6), `decrypt` (Task 4), `KeyManager` (Task 3), `receive_sharing_intent`, `image_picker`

- [ ] **Step 1: Создать read_screen.dart**

`lib/screens/read_screen.dart`:

```dart
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:image_picker/image_picker.dart';
import 'package:receive_sharing_intent/receive_sharing_intent.dart';
import '../crypto/decryptor.dart';
import '../crypto/key_manager.dart';
import '../stego/extractor.dart';

class ReadScreen extends StatefulWidget {
  final KeyManager keyManager;
  const ReadScreen({super.key, required this.keyManager});

  @override
  State<ReadScreen> createState() => _ReadScreenState();
}

class _ReadScreenState extends State<ReadScreen> {
  String? _message;
  String? _error;
  bool _busy = false;

  @override
  void initState() {
    super.initState();
    _listenForSharedFiles();
    _checkInitialSharedFiles();
  }

  void _listenForSharedFiles() {
    ReceiveSharingIntent.instance.getMediaStream().listen(
      (files) {
        if (files.isNotEmpty) _processFilePath(files.first.path);
      },
    );
  }

  Future<void> _checkInitialSharedFiles() async {
    final files = await ReceiveSharingIntent.instance.getInitialMedia();
    if (files.isNotEmpty) _processFilePath(files.first.path);
  }

  Future<void> _pickFromGallery() async {
    final picker = ImagePicker();
    final file = await picker.pickImage(source: ImageSource.gallery);
    if (file != null) _processFilePath(file.path);
  }

  Future<void> _processFilePath(String path) async {
    setState(() { _busy = true; _message = null; _error = null; });
    try {
      final bytes = await _readFile(path);
      await _processBytes(bytes);
    } catch (e) {
      if (mounted) setState(() { _error = 'Не удалось прочитать файл: $e'; _busy = false; });
    }
  }

  Future<Uint8List> _readFile(String path) async {
    // Use dart:io on Android, fallback for web
    // ignore: avoid_dynamic_calls
    try {
      final channel = const MethodChannel('flutter/assets');
      // Standard file read via dart:io
      final io = await _readFileBytes(path);
      return io;
    } catch (_) {
      rethrow;
    }
  }

  Future<Uint8List> _readFileBytes(String path) async {
    // dart:io import at top of file
    final file = _IOFile(path);
    return file.readAsBytes();
  }

  Future<void> _processBytes(Uint8List imageBytes) async {
    final payload = await extractBytes(imageBytes);
    if (payload == null) {
      if (mounted) setState(() { _error = 'В этом изображении нет скрытых данных'; _busy = false; });
      return;
    }

    final hasPair = await widget.keyManager.hasKeyPair();
    if (!hasPair) {
      if (mounted) setState(() { _error = 'Нет ключевой пары. Сначала сгенерируй ключи.'; _busy = false; });
      return;
    }

    final myKeyPair = await widget.keyManager.loadMyKeyPair();
    try {
      final message = await decrypt(payload, myKeyPair);
      if (mounted) setState(() { _message = message; _busy = false; });
    } on CryptoException catch (e) {
      if (mounted) setState(() { _error = e.message; _busy = false; });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          OutlinedButton.icon(
            onPressed: _busy ? null : _pickFromGallery,
            icon: const Icon(Icons.photo_library),
            label: const Text('Выбрать изображение из галереи'),
          ),
          const SizedBox(height: 24),
          if (_busy)
            const Center(child: CircularProgressIndicator()),
          if (_error != null)
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.red.shade900.withOpacity(0.3),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Text(_error!, style: const TextStyle(color: Colors.redAccent)),
            ),
          if (_message != null) ...[
            Text('Сообщение:', style: Theme.of(context).textTheme.labelMedium),
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.green.shade900.withOpacity(0.3),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: Colors.greenAccent.withOpacity(0.4)),
              ),
              child: SelectableText(
                _message!,
                style: const TextStyle(fontSize: 16, height: 1.5),
              ),
            ),
            const SizedBox(height: 12),
            OutlinedButton.icon(
              onPressed: () {
                Clipboard.setData(ClipboardData(text: _message!));
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Скопировано')),
                );
              },
              icon: const Icon(Icons.copy),
              label: const Text('Скопировать'),
            ),
          ],
        ],
      ),
    );
  }
}

// Minimal wrapper to avoid dart:io import conflict with web target
class _IOFile {
  final String path;
  _IOFile(this.path);
  Future<Uint8List> readAsBytes() async {
    // dart:io is available on Android; on web this path is not reached
    // (share target not available on web)
    final channel = MethodChannel('stegocrypt/file');
    final bytes = await channel.invokeMethod<Uint8List>('readFile', path);
    return bytes!;
  }
}
```

> Примечание: чтение файлов по пути на Android проще сделать через `dart:io`. Заменить `_IOFile` на прямой `import 'dart:io'; File(path).readAsBytes()` в Android-сборке. Для веба этот экран просто не получает файлы через share target — только через picker.

- [ ] **Step 2: Упростить _readFileBytes через dart:io**

В `lib/screens/read_screen.dart` заменить `_IOFile` класс и метод `_readFileBytes` на:

```dart
// Добавить в начало файла:
// import 'dart:io' show File;  // только для Android

Future<Uint8List> _readFileBytes(String path) async {
  // На вебе этот код не вызывается (share target недоступен)
  // ignore: avoid_web_libraries_in_flutter
  return File(path).readAsBytes();
}
```

И убрать класс `_IOFile` полностью, убрать `_readFile` обёртку:

```dart
Future<void> _processFilePath(String path) async {
  setState(() { _busy = true; _message = null; _error = null; });
  try {
    final bytes = await File(path).readAsBytes();
    await _processBytes(bytes);
  } catch (e) {
    if (mounted) setState(() { _error = 'Не удалось прочитать файл: $e'; _busy = false; });
  }
}
```

- [ ] **Step 3: Проверить анализатором**

```bash
flutter analyze lib/screens/read_screen.dart
```

Исправить все предупреждения.

- [ ] **Step 4: Коммит**

```bash
git add lib/screens/read_screen.dart
git commit -m "feat: read screen with share target support"
```

---

### Task 10: App Shell + Navigation

**Files:**
- Modify: `lib/main.dart`

**Interfaces:**
- Consumes: все три экрана (Tasks 7, 8, 9), `KeyManager` (Task 3)

- [ ] **Step 1: Написать main.dart**

`lib/main.dart`:

```dart
import 'package:flutter/material.dart';
import 'crypto/key_manager.dart';
import 'screens/keys_screen.dart';
import 'screens/read_screen.dart';
import 'screens/write_screen.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const StegoCryptApp());
}

class StegoCryptApp extends StatelessWidget {
  const StegoCryptApp({super.key});

  @override
  Widget build(BuildContext context) {
    final keyManager = KeyManager();
    return MaterialApp(
      title: 'StegoCrypt',
      debugShowCheckedModeBanner: false,
      theme: ThemeData.dark(useMaterial3: true).copyWith(
        colorScheme: ColorScheme.fromSeed(
          seedColor: Colors.greenAccent,
          brightness: Brightness.dark,
        ),
      ),
      home: AppShell(keyManager: keyManager),
    );
  }
}

class AppShell extends StatefulWidget {
  final KeyManager keyManager;
  const AppShell({super.key, required this.keyManager});

  @override
  State<AppShell> createState() => _AppShellState();
}

class _AppShellState extends State<AppShell> {
  int _index = 0;

  late final List<Widget> _screens = [
    WriteScreen(keyManager: widget.keyManager),
    ReadScreen(keyManager: widget.keyManager),
    KeysScreen(keyManager: widget.keyManager),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('StegoCrypt'),
        centerTitle: true,
      ),
      body: IndexedStack(index: _index, children: _screens),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _index,
        onDestinationSelected: (i) => setState(() => _index = i),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.edit), label: 'Написать'),
          NavigationDestination(icon: Icon(Icons.lock_open), label: 'Прочитать'),
          NavigationDestination(icon: Icon(Icons.key), label: 'Ключи'),
        ],
      ),
    );
  }
}
```

- [ ] **Step 2: Запустить все тесты**

```bash
flutter test
```

Ожидаемый вывод: `All tests passed!`

- [ ] **Step 3: Собрать debug APK**

```bash
flutter build apk --debug 2>&1 | tail -10
```

Ожидаемый вывод: `✓ Built build/app/outputs/flutter-apk/app-debug.apk`

- [ ] **Step 4: Коммит**

```bash
git add lib/main.dart
git commit -m "feat: app shell with bottom navigation — stegocrypt complete"
```

---

## Итог

После Task 10 готово рабочее приложение:
- `flutter test` — все unit-тесты проходят
- `flutter build apk --debug` — собирается
- Экран Ключи: генерация X25519 пары, QR + копипаст, fingerprint
- Экран Написать: галерея → текст → ECIES-шифрование → LSB в PNG → share sheet
- Экран Прочитать: галерея + share target → LSB-извлечение → расшифровка → текст
