import type { Metadata } from 'next';
import { LegalPage, Section } from '@/components/legal';

export const metadata: Metadata = {
  title: 'Terms of Service',
  description: 'The terms that govern your use of Career Operator.',
  alternates: { canonical: '/terms' },
  robots: { index: true, follow: true },
};

export default function TermsPage() {
  return (
    <LegalPage title="Terms of Service" updated="June 28, 2026">
      <p>
        These Terms govern your use of Career Operator. By creating an account or using the
        service, you agree to them. If you do not agree, please do not use the service.
      </p>

      <Section heading="The service">
        <p>
          Career Operator provides job-search tools: fit scoring, AI interview prep, an AI
          career coach, and a pipeline tracker. Features and limits depend on your plan and may
          change as we improve the product.
        </p>
      </Section>

      <Section heading="Your account">
        <p>
          You are responsible for keeping your login credentials secure and for activity under
          your account. Provide accurate information, and notify us if you believe your account
          has been compromised. You must be at least 16 years old to use the service.
        </p>
      </Section>

      <Section heading="Acceptable use">
        <p>You agree not to:</p>
        <ul className="list-disc space-y-1 pl-5">
          <li>Abuse, overload, scrape, or attempt to disrupt the service or its infrastructure.</li>
          <li>Reverse engineer or attempt to bypass usage limits, paywalls, or security controls.</li>
          <li>Upload unlawful content or use the service to violate others&rsquo; rights.</li>
        </ul>
      </Section>

      <Section heading="Plans, billing &amp; cancellation">
        <p>
          Free and paid plans are described on our pricing page. Paid subscriptions are billed
          in advance through our payment processor and renew automatically until cancelled. You
          can cancel anytime; your paid features remain until the end of the current billing
          period. On mobile, subscriptions purchased through the App Store or Google Play are
          managed and cancelled through your app-store account, per that store&rsquo;s rules.
        </p>
      </Section>

      <Section heading="AI-generated content">
        <p>
          Fit scores, prep packs, and coach responses are generated with the help of AI and are
          provided for guidance only. They can be incomplete or wrong, are not professional,
          legal, or financial advice, and we do not guarantee any particular outcome (such as
          getting an interview or an offer). Use your own judgment before relying on them.
        </p>
      </Section>

      <Section heading="Your content">
        <p>
          You retain ownership of the content you provide (such as job details and resume text).
          You grant us a limited license to process that content solely to operate the service
          for you — including sending the relevant parts to our AI provider to generate results,
          as described in our{' '}
          <a className="text-indigo-400 hover:text-indigo-300" href="/privacy">
            Privacy Policy
          </a>
          .
        </p>
      </Section>

      <Section heading="Disclaimers &amp; limitation of liability">
        <p>
          The service is provided &ldquo;as is&rdquo; without warranties of any kind, to the
          fullest extent permitted by law. To the extent permitted by law, our total liability
          for any claim relating to the service is limited to the amount you paid us in the
          twelve months before the claim, and we are not liable for indirect or consequential
          damages.
        </p>
      </Section>

      <Section heading="Termination">
        <p>
          You can stop using the service and delete your account at any time. We may suspend or
          terminate access if you breach these Terms or to protect the service and its users.
        </p>
      </Section>

      <Section heading="Changes to these terms">
        <p>
          We may update these Terms as the product evolves. We will revise the &ldquo;Last
          updated&rdquo; date above and, for material changes, provide a more prominent notice.
          Continued use after changes means you accept the updated Terms.
        </p>
      </Section>

      <Section heading="Contact">
        <p>
          Questions about these Terms? Email{' '}
          <a className="text-indigo-400 hover:text-indigo-300" href="mailto:support@careeroperator.app">
            support@careeroperator.app
          </a>
          .
        </p>
      </Section>
    </LegalPage>
  );
}
