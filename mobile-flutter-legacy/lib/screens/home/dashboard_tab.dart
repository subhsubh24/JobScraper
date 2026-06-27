import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../models/job.dart';
import '../../providers/auth_provider.dart';
import '../../providers/jobs_provider.dart';
import '../../theme.dart';
import '../../widgets/job_card.dart';
import '../../widgets/stat_card.dart';

class DashboardTab extends StatelessWidget {
  const DashboardTab({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Dashboard'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () {
              context.read<JobsProvider>().loadJobs();
              context.read<JobsProvider>().loadPipelineStats();
            },
          ),
        ],
      ),
      body: Consumer2<AuthProvider, JobsProvider>(
        builder: (context, auth, jobs, _) {
          if (jobs.isLoading && jobs.jobs.isEmpty) {
            return const Center(child: CircularProgressIndicator());
          }

          return RefreshIndicator(
            onRefresh: () async {
              await jobs.loadJobs();
              await jobs.loadPipelineStats();
            },
            child: ListView(
              padding: const EdgeInsets.all(16),
              children: [
                // Welcome message
                Text(
                  'Welcome back${auth.user?.fullName != null ? ", ${auth.user!.fullName}" : ""}!',
                  style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                ),
                const SizedBox(height: 8),
                Text(
                  auth.isPremium
                      ? 'Premium Member'
                      : '${auth.user?.jobsRemaining ?? 5} jobs remaining this month',
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        color: auth.isPremium
                            ? AppTheme.successColor
                            : Colors.grey,
                      ),
                ),
                const SizedBox(height: 24),

                // Pipeline stats
                Text(
                  'Pipeline Overview',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                ),
                const SizedBox(height: 12),
                Row(
                  children: [
                    Expanded(
                      child: StatCard(
                        title: 'Saved',
                        value: jobs.savedJobs.length.toString(),
                        icon: Icons.bookmark_outline,
                        color: Colors.blue,
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: StatCard(
                        title: 'Applied',
                        value: jobs.appliedJobs.length.toString(),
                        icon: Icons.send_outlined,
                        color: Colors.orange,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                Row(
                  children: [
                    Expanded(
                      child: StatCard(
                        title: 'Interviewing',
                        value: jobs.interviewingJobs.length.toString(),
                        icon: Icons.people_outline,
                        color: Colors.purple,
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: StatCard(
                        title: 'Offers',
                        value: jobs.offerJobs.length.toString(),
                        icon: Icons.celebration_outlined,
                        color: Colors.green,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 24),

                // Top jobs
                if (jobs.topJobs.isNotEmpty) ...[
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        'Top Matches',
                        style:
                            Theme.of(context).textTheme.titleMedium?.copyWith(
                                  fontWeight: FontWeight.bold,
                                ),
                      ),
                      TextButton(
                        onPressed: () {
                          // Navigate to jobs tab
                        },
                        child: const Text('See all'),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  ...jobs.topJobs.take(3).map(
                        (job) => Padding(
                          padding: const EdgeInsets.only(bottom: 12),
                          child: JobCard(job: job),
                        ),
                      ),
                ],

                // Empty state
                if (jobs.jobs.isEmpty)
                  Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const SizedBox(height: 48),
                        Icon(
                          Icons.work_outline,
                          size: 64,
                          color: Colors.grey[400],
                        ),
                        const SizedBox(height: 16),
                        Text(
                          'No jobs yet',
                          style:
                              Theme.of(context).textTheme.titleLarge?.copyWith(
                                    color: Colors.grey[600],
                                  ),
                        ),
                        const SizedBox(height: 8),
                        Text(
                          'Add your first job to get started',
                          style:
                              Theme.of(context).textTheme.bodyMedium?.copyWith(
                                    color: Colors.grey,
                                  ),
                        ),
                        const SizedBox(height: 24),
                        ElevatedButton.icon(
                          onPressed: () {
                            // Navigate to add job
                          },
                          icon: const Icon(Icons.add),
                          label: const Text('Add Job'),
                        ),
                      ],
                    ),
                  ),
              ],
            ),
          );
        },
      ),
    );
  }
}
