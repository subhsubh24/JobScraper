enum ApplicationStatus {
  saved,
  applied,
  phoneScreen,
  interview,
  offer,
  rejected,
  withdrawn,
}

extension ApplicationStatusExtension on ApplicationStatus {
  String get displayName {
    switch (this) {
      case ApplicationStatus.saved:
        return 'Saved';
      case ApplicationStatus.applied:
        return 'Applied';
      case ApplicationStatus.phoneScreen:
        return 'Phone Screen';
      case ApplicationStatus.interview:
        return 'Interview';
      case ApplicationStatus.offer:
        return 'Offer';
      case ApplicationStatus.rejected:
        return 'Rejected';
      case ApplicationStatus.withdrawn:
        return 'Withdrawn';
    }
  }

  String get apiValue {
    switch (this) {
      case ApplicationStatus.saved:
        return 'saved';
      case ApplicationStatus.applied:
        return 'applied';
      case ApplicationStatus.phoneScreen:
        return 'phone_screen';
      case ApplicationStatus.interview:
        return 'interview';
      case ApplicationStatus.offer:
        return 'offer';
      case ApplicationStatus.rejected:
        return 'rejected';
      case ApplicationStatus.withdrawn:
        return 'withdrawn';
    }
  }

  static ApplicationStatus fromString(String value) {
    switch (value) {
      case 'saved':
        return ApplicationStatus.saved;
      case 'applied':
        return ApplicationStatus.applied;
      case 'phone_screen':
        return ApplicationStatus.phoneScreen;
      case 'interview':
        return ApplicationStatus.interview;
      case 'offer':
        return ApplicationStatus.offer;
      case 'rejected':
        return ApplicationStatus.rejected;
      case 'withdrawn':
        return ApplicationStatus.withdrawn;
      default:
        return ApplicationStatus.saved;
    }
  }
}

class JobScore {
  final double overallScore;
  final double? skillsMatch;
  final List<String> matchingSkills;
  final List<String> missingSkills;
  final String? explanation;

  JobScore({
    required this.overallScore,
    this.skillsMatch,
    this.matchingSkills = const [],
    this.missingSkills = const [],
    this.explanation,
  });

  factory JobScore.fromJson(Map<String, dynamic> json) {
    return JobScore(
      overallScore: (json['overall_score'] ?? 0).toDouble(),
      skillsMatch: json['skills_match']?.toDouble(),
      matchingSkills: List<String>.from(json['matching_skills'] ?? []),
      missingSkills: List<String>.from(json['missing_skills'] ?? []),
      explanation: json['score_explanation'],
    );
  }
}

class Job {
  final String id;
  final String title;
  final String companyName;
  final String? location;
  final String? remoteType;
  final String? description;
  final String? requirements;
  final int? salaryMin;
  final int? salaryMax;
  final String? url;
  final ApplicationStatus status;
  final JobScore? score;
  final DateTime createdAt;
  final String? notes;

  Job({
    required this.id,
    required this.title,
    required this.companyName,
    this.location,
    this.remoteType,
    this.description,
    this.requirements,
    this.salaryMin,
    this.salaryMax,
    this.url,
    this.status = ApplicationStatus.saved,
    this.score,
    required this.createdAt,
    this.notes,
  });

  factory Job.fromJson(Map<String, dynamic> json) {
    return Job(
      id: json['id'],
      title: json['title'],
      companyName: json['company_name'] ?? 'Unknown Company',
      location: json['location'],
      remoteType: json['remote_type'],
      description: json['description'],
      requirements: json['requirements'],
      salaryMin: json['salary_min'],
      salaryMax: json['salary_max'],
      url: json['url'],
      status: ApplicationStatusExtension.fromString(
          json['application_status'] ?? json['status'] ?? 'saved'),
      score: json['score'] != null ? JobScore.fromJson(json['score']) : null,
      createdAt: DateTime.parse(json['created_at']),
      notes: json['notes'],
    );
  }

  String get salaryRange {
    if (salaryMin == null && salaryMax == null) return 'Not specified';
    if (salaryMin != null && salaryMax != null) {
      return '\$${_formatSalary(salaryMin!)} - \$${_formatSalary(salaryMax!)}';
    }
    if (salaryMin != null) return '\$${_formatSalary(salaryMin!)}+';
    return 'Up to \$${_formatSalary(salaryMax!)}';
  }

  String _formatSalary(int amount) {
    if (amount >= 1000) {
      return '${(amount / 1000).toStringAsFixed(0)}K';
    }
    return amount.toString();
  }

  Job copyWith({
    ApplicationStatus? status,
    String? notes,
    JobScore? score,
  }) {
    return Job(
      id: id,
      title: title,
      companyName: companyName,
      location: location,
      remoteType: remoteType,
      description: description,
      requirements: requirements,
      salaryMin: salaryMin,
      salaryMax: salaryMax,
      url: url,
      status: status ?? this.status,
      score: score ?? this.score,
      createdAt: createdAt,
      notes: notes ?? this.notes,
    );
  }
}
