import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../providers/auth_provider.dart';
import '../../theme.dart';

class SettingsScreen extends StatelessWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Profile'),
      ),
      body: Consumer<AuthProvider>(
        builder: (context, auth, _) {
          final user = auth.user;

          return ListView(
            children: [
              // Profile header
              Container(
                padding: const EdgeInsets.all(24),
                child: Column(
                  children: [
                    CircleAvatar(
                      radius: 50,
                      backgroundColor:
                          Theme.of(context).colorScheme.primaryContainer,
                      child: Text(
                        user?.fullName?.isNotEmpty == true
                            ? user!.fullName![0].toUpperCase()
                            : user?.email[0].toUpperCase() ?? '?',
                        style: const TextStyle(fontSize: 36),
                      ),
                    ),
                    const SizedBox(height: 16),
                    Text(
                      user?.fullName ?? 'User',
                      style:
                          Theme.of(context).textTheme.headlineSmall?.copyWith(
                                fontWeight: FontWeight.bold,
                              ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      user?.email ?? '',
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                            color: Colors.grey,
                          ),
                    ),
                    const SizedBox(height: 12),
                    if (auth.isPremium)
                      Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 16,
                          vertical: 8,
                        ),
                        decoration: BoxDecoration(
                          color: AppTheme.successColor.withOpacity(0.2),
                          borderRadius: BorderRadius.circular(20),
                        ),
                        child: const Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Icon(Icons.star, color: AppTheme.successColor, size: 16),
                            SizedBox(width: 4),
                            Text(
                              'Premium',
                              style: TextStyle(
                                color: AppTheme.successColor,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ],
                        ),
                      ),
                  ],
                ),
              ),

              const Divider(),

              // Upgrade to premium (if free)
              if (!auth.isPremium)
                ListTile(
                  leading: Container(
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: AppTheme.accentColor.withOpacity(0.2),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: const Icon(Icons.star, color: AppTheme.accentColor),
                  ),
                  title: const Text('Upgrade to Premium'),
                  subtitle: const Text('Unlimited jobs & prep packs - \$4.99'),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () {
                    _showUpgradeDialog(context);
                  },
                ),

              // Usage stats (if free)
              if (!auth.isPremium) ...[
                ListTile(
                  leading: Container(
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: Colors.blue.withOpacity(0.2),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: const Icon(Icons.analytics, color: Colors.blue),
                  ),
                  title: const Text('Usage This Month'),
                  subtitle: Text(
                    'Jobs: ${user?.jobsAddedThisMonth ?? 0}/5 • Prep Packs: ${user?.prepPacksThisMonth ?? 0}/1',
                  ),
                ),
                const Divider(),
              ],

              // Resume
              ListTile(
                leading: Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: Colors.purple.withOpacity(0.2),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: const Icon(Icons.description, color: Colors.purple),
                ),
                title: const Text('My Resume'),
                subtitle: Text(
                  user?.resumeText != null ? 'Uploaded' : 'Not uploaded',
                ),
                trailing: const Icon(Icons.chevron_right),
                onTap: () {
                  _showResumeDialog(context);
                },
              ),

              const Divider(),

              // Settings
              ListTile(
                leading: Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: Colors.grey.withOpacity(0.2),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: const Icon(Icons.notifications, color: Colors.grey),
                ),
                title: const Text('Notifications'),
                trailing: Switch(
                  value: true,
                  onChanged: (value) {},
                ),
              ),

              ListTile(
                leading: Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: Colors.grey.withOpacity(0.2),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: const Icon(Icons.dark_mode, color: Colors.grey),
                ),
                title: const Text('Dark Mode'),
                subtitle: const Text('System default'),
                trailing: const Icon(Icons.chevron_right),
              ),

              const Divider(),

              // Support
              ListTile(
                leading: Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: Colors.green.withOpacity(0.2),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: const Icon(Icons.help, color: Colors.green),
                ),
                title: const Text('Help & Support'),
                trailing: const Icon(Icons.chevron_right),
              ),

              ListTile(
                leading: Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: Colors.teal.withOpacity(0.2),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: const Icon(Icons.privacy_tip, color: Colors.teal),
                ),
                title: const Text('Privacy Policy'),
                trailing: const Icon(Icons.chevron_right),
              ),

              const Divider(),

              // Logout
              ListTile(
                leading: Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: Colors.red.withOpacity(0.2),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: const Icon(Icons.logout, color: Colors.red),
                ),
                title: const Text('Sign Out', style: TextStyle(color: Colors.red)),
                onTap: () {
                  _showLogoutDialog(context);
                },
              ),

              const SizedBox(height: 24),
              Center(
                child: Text(
                  'Career Operator v1.0.0',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: Colors.grey,
                      ),
                ),
              ),
              const SizedBox(height: 24),
            ],
          );
        },
      ),
    );
  }

  void _showUpgradeDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: const Text('Upgrade to Premium'),
          content: const Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Get unlimited access for just \$4.99 (one-time):'),
              SizedBox(height: 16),
              Row(children: [Icon(Icons.check, color: Colors.green), SizedBox(width: 8), Text('Unlimited job tracking')]),
              SizedBox(height: 8),
              Row(children: [Icon(Icons.check, color: Colors.green), SizedBox(width: 8), Text('Unlimited prep packs')]),
              SizedBox(height: 8),
              Row(children: [Icon(Icons.check, color: Colors.green), SizedBox(width: 8), Text('Unlimited AI coach')]),
              SizedBox(height: 8),
              Row(children: [Icon(Icons.check, color: Colors.green), SizedBox(width: 8), Text('No ads, ever')]),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Maybe Later'),
            ),
            ElevatedButton(
              onPressed: () {
                // TODO: Implement in-app purchase
                Navigator.pop(context);
              },
              child: const Text('Buy \$4.99'),
            ),
          ],
        );
      },
    );
  }

  void _showResumeDialog(BuildContext context) {
    final controller = TextEditingController();

    showDialog(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: const Text('Update Resume'),
          content: TextField(
            controller: controller,
            maxLines: 10,
            decoration: const InputDecoration(
              hintText: 'Paste your resume text here...',
              border: OutlineInputBorder(),
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Cancel'),
            ),
            ElevatedButton(
              onPressed: () {
                // TODO: Save resume
                Navigator.pop(context);
              },
              child: const Text('Save'),
            ),
          ],
        );
      },
    );
  }

  void _showLogoutDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: const Text('Sign Out'),
          content: const Text('Are you sure you want to sign out?'),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Cancel'),
            ),
            ElevatedButton(
              onPressed: () {
                context.read<AuthProvider>().logout();
                Navigator.pop(context);
              },
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.red,
              ),
              child: const Text('Sign Out'),
            ),
          ],
        );
      },
    );
  }
}
