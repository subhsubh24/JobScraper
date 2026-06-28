import type { Metadata } from 'next';
import { LegalPage, Section } from '@/components/legal';

export const metadata: Metadata = {
  title: 'Privacy Policy',
  description: 'How Career Operator collects, uses, and protects your data.',
  alternates: { canonical: '/privacy' },
  robots: { index: true, follow: true },
};

export default function PrivacyPage() {
  return (
    <LegalPage title="Privacy Policy" updated="June 28, 2026">
      <p>
        Career Operator (&ldquo;we,&rdquo; &ldquo;us&rdquo;) helps you run your job search:
        scoring roles against your background, generating interview prep, and tracking your
        pipeline. This policy explains what we collect, why, and the choices you have. We aim
        to collect only what the product needs to work, and we do not sell your personal data.
      </p>

      <Section heading="Information you provide">
        <p>When you use Career Operator, you may give us:</p>
        <ul className="list-disc space-y-1 pl-5">
          <li>
            <strong>Account details</strong> — your email address and a password (stored only
            as a salted hash, never in plain text), and an optional display name.
          </li>
          <li>
            <strong>Job-search data</strong> — the roles you add (title, company, description,
            location, compensation), application statuses, and notes you record.
          </li>
          <li>
            <strong>Profile / resume text</strong> — if you choose to provide it, so we can
            score how well a role fits you. To do this we also generate and store a numeric
            embedding (a vector representation) of your resume and of job descriptions; see
            &ldquo;AI processing&rdquo; below.
          </li>
          <li>
            <strong>AI coach messages</strong> — the messages you send to the AI career coach.
          </li>
        </ul>
      </Section>

      <Section heading="How we use your information">
        <ul className="list-disc space-y-1 pl-5">
          <li>To provide the core features: fit scoring, interview prep, the AI coach, and your pipeline CRM.</li>
          <li>To enforce free-tier limits and, if you subscribe, manage your subscription.</li>
          <li>To secure the service (rate limiting, abuse prevention) and fix problems.</li>
        </ul>
        <p>
          We do <strong>not</strong> sell your personal data, and we do not use it to serve
          third-party advertising.
        </p>
      </Section>

      <Section heading="AI processing">
        <p>
          To generate fit scores, prep packs, and coach replies, the relevant content you
          provide (such as a job description, your resume text, or a coach message) is sent to
          our AI provider, Google (Gemini API), to produce a response. We also send your resume
          and job-description text to Google&rsquo;s embedding API to generate the vector
          representations described above, which we store to power fit scoring. When no AI
          provider is configured, the product falls back to a non-AI heuristic where possible
          rather than failing. We do not use your data to train our own models.
        </p>
      </Section>

      <Section heading="Service providers we rely on">
        <ul className="list-disc space-y-1 pl-5">
          <li><strong>Google (Gemini API)</strong> — AI scoring, prep, and coaching.</li>
          <li><strong>Vercel</strong> — application hosting.</li>
          <li><strong>Neon</strong> — managed PostgreSQL database.</li>
          <li><strong>Stripe</strong> — payment processing for subscriptions. This is not active yet; once paid plans launch, card details will go directly to Stripe and we will never see or store your full card number.</li>
        </ul>
        <p>These providers process data on our behalf under their own terms and security practices.</p>
      </Section>

      <Section heading="Data retention &amp; deletion">
        <p>
          We keep your data while your account is active. You can permanently delete your
          account at any time from the app&rsquo;s Settings (&ldquo;Delete account&rdquo;) or
          by contacting us. Deletion removes your account and the data tied to it — your jobs,
          scores, applications, prep artifacts, and coach history — and cannot be undone.
        </p>
      </Section>

      <Section heading="Security">
        <p>
          Connections use TLS, passwords are stored only as salted hashes, and expensive and
          authentication endpoints are rate-limited. No system is perfectly secure, but we work
          to protect your data and limit what we collect in the first place.
        </p>
      </Section>

      <Section heading="Your rights">
        <p>
          Depending on where you live, you may have rights to access, correct, export, or delete
          your personal data. You can exercise deletion directly in-app; for other requests,
          contact us at the address below and we will respond within a reasonable time.
        </p>
      </Section>

      <Section heading="Children">
        <p>
          Career Operator is intended for adults in the workforce and is not directed to
          children under 16. We do not knowingly collect data from children.
        </p>
      </Section>

      <Section heading="Changes to this policy">
        <p>
          We may update this policy as the product evolves. We will revise the &ldquo;Last
          updated&rdquo; date above and, for material changes, provide a more prominent notice.
        </p>
      </Section>

      <Section heading="Contact">
        <p>
          Questions about privacy? Email{' '}
          <a className="text-indigo-400 hover:text-indigo-300" href="mailto:privacy@careeroperator.app">
            privacy@careeroperator.app
          </a>
          .
        </p>
      </Section>
    </LegalPage>
  );
}
