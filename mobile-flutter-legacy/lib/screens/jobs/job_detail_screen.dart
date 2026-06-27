import 'package:flutter/material.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:provider/provider.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../models/job.dart';
import '../../providers/jobs_provider.dart';
import '../../theme.dart';

class JobDetailScreen extends StatefulWidget {
  final String jobId;

  const JobDetailScreen({super.key, required this.jobId});

  @override
  State<JobDetailScreen> createState() => _JobDetailScreenState();
}

class _JobDetailScreenState extends State<JobDetailScreen> {
  String? _prepPackContent;
  bool _isGeneratingPrepPack = false;

  @override
  Widget build(BuildContext context) {
    return Consumer<JobsProvider>(
      builder: (context, jobs, _) {
        final job = jobs.getJobById(widget.jobId);

        if (job == null) {
          return Scaffold(
            appBar: AppBar(),
            body: const Center(child: Text('Job not found')),
          );
        }

        return Scaffold(
          appBar: AppBar(
            title: const Text('Job Details'),
            actions: [
              if (job.url != null)
                IconButton(
                  icon: const Icon(Icons.open_in_new),
                  onPressed: () => _launchUrl(job.url!),
                ),
              PopupMenuButton(
                itemBuilder: (context) => [
                  const PopupMenuItem(
                    value: 'status',
                    child: Text('Update Status'),
                  ),
                ],
                onSelected: (value) {
                  if (value == 'status') {
                    _showStatusPicker(context, job);
                  }
                },
              ),
            ],
          ),
          body: SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Header
                Text(
                  job.title,
                  style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                ),
                const SizedBox(height: 8),
                Text(
                  job.companyName,
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        color: Theme.of(context).colorScheme.primary,
                      ),
                ),
                const SizedBox(height: 4),
                if (job.location != null)
                  Row(
                    children: [
                      const Icon(Icons.location_on_outlined, size: 16),
                      const SizedBox(width: 4),
                      Text(job.location!),
                    ],
                  ),
                const SizedBox(height: 16),

                // Score card
                if (job.score != null) _buildScoreCard(job),
                const SizedBox(height: 16),

                // Status chip
                Row(
                  children: [
                    Chip(
                      label: Text(job.status.displayName),
                      backgroundColor:
                          _getStatusColor(job.status).withOpacity(0.2),
                    ),
                    const SizedBox(width: 8),
                    if (job.salaryMin != null || job.salaryMax != null)
                      Chip(
                        avatar: const Icon(Icons.attach_money, size: 16),
                        label: Text(job.salaryRange),
                      ),
                  ],
                ),
                const SizedBox(height: 24),

                // Prep pack section
                _buildPrepPackSection(job),
                const SizedBox(height: 24),

                // Description
                if (job.description != null) ...[
                  Text(
                    'Description',
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                          fontWeight: FontWeight.bold,
                        ),
                  ),
                  const SizedBox(height: 8),
                  Text(job.description!),
                  const SizedBox(height: 24),
                ],

                // Requirements
                if (job.requirements != null) ...[
                  Text(
                    'Requirements',
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                          fontWeight: FontWeight.bold,
                        ),
                  ),
                  const SizedBox(height: 8),
                  Text(job.requirements!),
                ],
              ],
            ),
          ),
          bottomNavigationBar: SafeArea(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Row(
                children: [
                  Expanded(
                    child: OutlinedButton(
                      onPressed: () => _showStatusPicker(context, job),
                      child: const Text('Update Status'),
                    ),
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: ElevatedButton(
                      onPressed: job.url != null ? () => _launchUrl(job.url!) : null,
                      child: const Text('Apply'),
                    ),
                  ),
                ],
              ),
            ),
          ),
        );
      },
    );
  }

  Widget _buildScoreCard(Job job) {
    final score = job.score!;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  width: 60,
                  height: 60,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: AppTheme.getScoreColor(score.overallScore)
                        .withOpacity(0.2),
                  ),
                  child: Center(
                    child: Text(
                      score.overallScore.toStringAsFixed(0),
                      style: TextStyle(
                        fontSize: 24,
                        fontWeight: FontWeight.bold,
                        color: AppTheme.getScoreColor(score.overallScore),
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Match Score',
                        style: TextStyle(fontWeight: FontWeight.bold),
                      ),
                      if (score.explanation != null)
                        Text(
                          score.explanation!,
                          style: const TextStyle(fontSize: 12),
                        ),
                    ],
                  ),
                ),
              ],
            ),
            if (score.matchingSkills.isNotEmpty) ...[
              const SizedBox(height: 12),
              Wrap(
                spacing: 4,
                runSpacing: 4,
                children: score.matchingSkills
                    .map((skill) => Chip(
                          label: Text(skill, style: const TextStyle(fontSize: 12)),
                          backgroundColor: Colors.green.withOpacity(0.2),
                          visualDensity: VisualDensity.compact,
                        ))
                    .toList(),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildPrepPackSection(Job job) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.school_outlined),
                const SizedBox(width: 8),
                Text(
                  'Interview Prep Pack',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            if (_prepPackContent != null) ...[
              MarkdownBody(data: _prepPackContent!),
            ] else ...[
              const Text(
                'Generate an AI-powered prep pack with interview questions, company research, and a study plan.',
              ),
              const SizedBox(height: 12),
              ElevatedButton.icon(
                onPressed: _isGeneratingPrepPack
                    ? null
                    : () => _generatePrepPack(job.id),
                icon: _isGeneratingPrepPack
                    ? const SizedBox(
                        width: 16,
                        height: 16,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.auto_awesome),
                label: Text(
                    _isGeneratingPrepPack ? 'Generating...' : 'Generate Prep Pack'),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Future<void> _generatePrepPack(String jobId) async {
    setState(() => _isGeneratingPrepPack = true);

    final content = await context.read<JobsProvider>().generatePrepPack(jobId);

    if (mounted) {
      setState(() {
        _prepPackContent = content;
        _isGeneratingPrepPack = false;
      });
    }
  }

  void _showStatusPicker(BuildContext context, Job job) {
    showModalBottomSheet(
      context: context,
      builder: (context) {
        return SafeArea(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: ApplicationStatus.values.map((status) {
              return ListTile(
                leading: Icon(
                  _getStatusIcon(status),
                  color: _getStatusColor(status),
                ),
                title: Text(status.displayName),
                selected: job.status == status,
                onTap: () async {
                  Navigator.pop(context);
                  await context
                      .read<JobsProvider>()
                      .updateJobStatus(job.id, status);
                },
              );
            }).toList(),
          ),
        );
      },
    );
  }

  Color _getStatusColor(ApplicationStatus status) {
    switch (status) {
      case ApplicationStatus.saved:
        return Colors.blue;
      case ApplicationStatus.applied:
        return Colors.orange;
      case ApplicationStatus.phoneScreen:
      case ApplicationStatus.interview:
        return Colors.purple;
      case ApplicationStatus.offer:
        return Colors.green;
      case ApplicationStatus.rejected:
        return Colors.red;
      case ApplicationStatus.withdrawn:
        return Colors.grey;
    }
  }

  IconData _getStatusIcon(ApplicationStatus status) {
    switch (status) {
      case ApplicationStatus.saved:
        return Icons.bookmark;
      case ApplicationStatus.applied:
        return Icons.send;
      case ApplicationStatus.phoneScreen:
        return Icons.phone;
      case ApplicationStatus.interview:
        return Icons.people;
      case ApplicationStatus.offer:
        return Icons.celebration;
      case ApplicationStatus.rejected:
        return Icons.cancel;
      case ApplicationStatus.withdrawn:
        return Icons.undo;
    }
  }

  Future<void> _launchUrl(String url) async {
    final uri = Uri.parse(url);
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    }
  }
}
