import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'providers/auth_provider.dart';
import 'providers/jobs_provider.dart';
import 'providers/coach_provider.dart';
import 'screens/auth/login_screen.dart';
import 'screens/home/home_screen.dart';
import 'services/api_client.dart';
import 'theme.dart';

void main() {
  runApp(const CareerOperatorApp());
}

class CareerOperatorApp extends StatelessWidget {
  const CareerOperatorApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        Provider<ApiClient>(create: (_) => ApiClient()),
        ChangeNotifierProxyProvider<ApiClient, AuthProvider>(
          create: (context) => AuthProvider(context.read<ApiClient>()),
          update: (context, api, auth) => auth!..updateApi(api),
        ),
        ChangeNotifierProxyProvider<ApiClient, JobsProvider>(
          create: (context) => JobsProvider(context.read<ApiClient>()),
          update: (context, api, jobs) => jobs!..updateApi(api),
        ),
        ChangeNotifierProxyProvider<ApiClient, CoachProvider>(
          create: (context) => CoachProvider(context.read<ApiClient>()),
          update: (context, api, coach) => coach!..updateApi(api),
        ),
      ],
      child: Consumer<AuthProvider>(
        builder: (context, auth, _) {
          return MaterialApp(
            title: 'Career Operator',
            theme: AppTheme.lightTheme,
            darkTheme: AppTheme.darkTheme,
            themeMode: ThemeMode.system,
            debugShowCheckedModeBanner: false,
            home: auth.isAuthenticated
                ? const HomeScreen()
                : const LoginScreen(),
          );
        },
      ),
    );
  }
}
