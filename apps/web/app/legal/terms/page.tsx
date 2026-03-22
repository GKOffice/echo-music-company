import type { Metadata } from "next";
import Link from "next/link";
import Navbar from "@/components/Navbar";

export const metadata: Metadata = {
  title: "Terms of Service — Melodio",
  description:
    "Melodio Terms of Service. Read the terms governing your use of the Melodio platform, artist agreements, Melodio Points, and more.",
};

const LAST_UPDATED = "March 21, 2026";

export default function TermsPage() {
  return (
    <main className="min-h-screen bg-[#0a0a0f] text-[#f9fafb]">
      <Navbar />

      <div className="max-w-3xl mx-auto px-4 pt-28 pb-20">
        {/* Header */}
        <div className="mb-12">
          <div className="inline-block bg-[#f59e0b]/10 border border-[#f59e0b]/30 text-[#f59e0b] text-xs font-bold px-3 py-1.5 rounded-full mb-4">
            DRAFT — NOT YET LEGALLY BINDING
          </div>
          <h1 className="text-4xl font-black mb-3">Terms of Service</h1>
          <p className="text-[#9ca3af]">
            Last updated: {LAST_UPDATED}
          </p>
          <div className="mt-4 bg-[#f59e0b]/5 border border-[#f59e0b]/20 rounded-xl p-4 text-sm text-[#fbbf24]">
            This document is a <strong>working draft</strong> and has not been
            reviewed or approved by legal counsel. Sections marked with
            [ATTORNEY REVIEW REQUIRED] require professional legal review before
            publication. Do not rely on this document as legal advice.
          </div>
        </div>

        {/* TOS Content */}
        <div className="prose prose-invert max-w-none space-y-10 text-[#d1d5db] text-sm leading-relaxed [&_h2]:text-[#f9fafb] [&_h2]:text-xl [&_h2]:font-bold [&_h2]:mb-4 [&_h3]:text-[#f9fafb] [&_h3]:text-base [&_h3]:font-semibold [&_h3]:mb-2 [&_strong]:text-[#f9fafb] [&_ul]:list-disc [&_ul]:pl-5 [&_ul]:space-y-1 [&_ol]:list-decimal [&_ol]:pl-5 [&_ol]:space-y-1">

          {/* 1 */}
          <section>
            <h2>1. Acceptance of Terms</h2>
            <p>
              By accessing or using the Melodio platform (&quot;Service&quot;), operated by Melodio Inc.
              (&quot;Melodio,&quot; &quot;we,&quot; &quot;us,&quot; or &quot;our&quot;), you agree to be bound by these Terms of
              Service (&quot;Terms&quot;). If you do not agree to these Terms, do not use the Service.
            </p>
            <p>
              We reserve the right to update these Terms at any time. Material changes will be
              communicated via email or in-app notification at least 30 days before taking effect.
              Continued use of the Service after changes take effect constitutes acceptance.
            </p>
            <p className="text-[#f59e0b] text-xs font-semibold">[ATTORNEY REVIEW REQUIRED]</p>
          </section>

          {/* 2 */}
          <section>
            <h2>2. Account Registration and Eligibility</h2>
            <p>
              You must be at least 18 years of age to create an account on Melodio. By registering,
              you represent that you are of legal age in your jurisdiction and that the information
              you provide is accurate and complete.
            </p>
            <ul>
              <li>You are responsible for maintaining the security of your account credentials.</li>
              <li>You must not share your account or allow others to access it.</li>
              <li>You must promptly notify us of any unauthorized use of your account.</li>
              <li>We reserve the right to suspend or terminate accounts that violate these Terms.</li>
            </ul>
            <p className="text-[#f59e0b] text-xs font-semibold">[ATTORNEY REVIEW REQUIRED]</p>
          </section>

          {/* 3 */}
          <section>
            <h2>3. Artist Agreements</h2>
            <p>
              Melodio offers artists non-exclusive, per-song agreements. The key terms are:
            </p>
            <ul>
              <li><strong>Deal structure:</strong> 1-song non-exclusive agreements. No multi-album deals or long-term lock-ins.</li>
              <li><strong>Revenue split:</strong> 60% to the artist, 40% to Melodio for platform operations, distribution, marketing, and agent infrastructure.</li>
              <li><strong>Master ownership:</strong> Melodio holds the master recording license for a period of 5 years from the release date. After 5 years, full master rights revert to the artist at no cost.</li>
              <li><strong>Publishing:</strong> Artists retain 100% of their publishing rights. Melodio does not claim any ownership of underlying compositions.</li>
              <li><strong>Exclusivity:</strong> Agreements are non-exclusive. Artists are free to release music with other labels or independently while signed to Melodio.</li>
            </ul>
            <p className="text-[#f59e0b] text-xs font-semibold">[ATTORNEY REVIEW REQUIRED — Critical: revenue split, master reversion terms, and non-exclusivity clause need legal validation]</p>
          </section>

          {/* 4 */}
          <section>
            <h2>4. Publishing Terms</h2>
            <p>
              Melodio takes 0% publisher&apos;s share of your compositions. Our publishing administration terms are:
            </p>
            <ul>
              <li><strong>Publisher cut:</strong> 0% — Melodio does not take a publisher share.</li>
              <li><strong>Admin fee:</strong> 10% administrative fee on royalties collected through our publishing administration service.</li>
              <li><strong>Writer share:</strong> 90% of collected publishing royalties flow directly to the songwriter(s).</li>
              <li><strong>Collection scope:</strong> Performance, mechanical, sync, and digital royalties collected from 60+ PROs worldwide.</li>
            </ul>
            <p className="text-[#f59e0b] text-xs font-semibold">[ATTORNEY REVIEW REQUIRED — Verify admin fee structure complies with MLC and international PRO regulations]</p>
          </section>

          {/* 5 */}
          <section>
            <h2>5. Melodio Points</h2>
            <h3>5.1 Purchase Terms</h3>
            <p>
              Melodio Points represent a contractual right to receive a proportional share of
              streaming royalties generated by a specific artist&apos;s release catalog on the Melodio
              platform. Points are NOT securities, equity, or ownership in Melodio Inc. or any artist entity.
            </p>
            <ul>
              <li>Points are purchased at a price set by the artist and/or Melodio at the time of the drop.</li>
              <li>All purchases are final. No refunds are available once a Point purchase is confirmed.</li>
              <li>The number of Points available per artist drop is limited and determined by the artist&apos;s allocation.</li>
            </ul>

            <h3>5.2 Lock Period</h3>
            <p>
              All Melodio Points are subject to a mandatory 12-month holding period from the date
              of purchase. During this period, Points cannot be sold, transferred, or traded on the
              Melodio marketplace.
            </p>

            <h3>5.3 Royalty Distribution</h3>
            <p>
              Royalties are distributed to Point holders on a quarterly basis (March, June, September,
              December). Distributions are proportional to the number of Points held relative to the
              total Points issued for that artist.
            </p>

            <h3>5.4 No Guaranteed Returns</h3>
            <p>
              <strong>Melodio Points do not guarantee any return on investment.</strong> Royalty
              distributions depend on actual streaming revenue generated by the artist. Streaming
              revenue may fluctuate, decrease, or cease entirely. Past performance is not indicative
              of future results. You may lose some or all of the value of your Point purchase.
            </p>
            <p className="text-[#f59e0b] text-xs font-semibold">[ATTORNEY REVIEW REQUIRED — Critical: Points classification, securities law compliance (SEC, state regulators), no-guarantee disclaimers]</p>
          </section>

          {/* 6 */}
          <section>
            <h2>6. Points Exchange</h2>
            <ul>
              <li><strong>Trading:</strong> After the 12-month lock period, Points may be listed for sale on the Melodio marketplace at a price set by the seller.</li>
              <li><strong>Transfer restrictions:</strong> Points may only be transferred through the Melodio marketplace. Off-platform transfers are not supported and any attempted off-platform transfers are void.</li>
              <li><strong>Marketplace fee:</strong> A 5% transaction fee applies to all marketplace sales, deducted from the seller&apos;s proceeds.</li>
              <li><strong>Tax obligations:</strong> You are solely responsible for determining and fulfilling your tax obligations arising from Point purchases, royalty distributions, and marketplace sales. Melodio does not provide tax advice.</li>
            </ul>
            <p className="text-[#f59e0b] text-xs font-semibold">[ATTORNEY REVIEW REQUIRED — Securities classification of secondary market trading, money transmitter licensing, state-by-state compliance]</p>
          </section>

          {/* 7 */}
          <section>
            <h2>7. Content Guidelines</h2>
            <p>
              All content submitted to or distributed through Melodio must comply with the following:
            </p>
            <ul>
              <li>No hate speech, harassment, threats of violence, or content promoting discrimination based on race, gender, religion, sexual orientation, or disability.</li>
              <li>No unauthorized samples, loops, or interpolations. All content must be original or properly licensed/cleared.</li>
              <li>Artists must own or have all necessary rights to the content they submit.</li>
              <li>No content that infringes on any third party&apos;s intellectual property rights.</li>
              <li>No content that violates any applicable local, state, national, or international law.</li>
            </ul>
            <p>
              Melodio reserves the right to remove any content that violates these guidelines without
              prior notice.
            </p>
            <p className="text-[#f59e0b] text-xs font-semibold">[ATTORNEY REVIEW REQUIRED]</p>
          </section>

          {/* 8 */}
          <section>
            <h2>8. DMCA and Takedown Procedure</h2>
            <p>
              Melodio respects intellectual property rights and complies with the Digital Millennium
              Copyright Act (DMCA). If you believe content on our platform infringes your copyright:
            </p>
            <ol>
              <li>Send a written notice to our designated DMCA agent at <strong>legal@melodio.io</strong> containing:
                <ul>
                  <li>Identification of the copyrighted work claimed to be infringed.</li>
                  <li>Identification of the material to be removed with sufficient information for us to locate it.</li>
                  <li>Your contact information (name, address, email, phone).</li>
                  <li>A statement that you have a good faith belief the use is not authorized.</li>
                  <li>A statement under penalty of perjury that the information is accurate and you are authorized to act on behalf of the copyright owner.</li>
                  <li>Your physical or electronic signature.</li>
                </ul>
              </li>
              <li>Upon receiving a valid notice, we will promptly remove or disable access to the material.</li>
              <li>We will notify the content uploader, who may submit a counter-notification.</li>
            </ol>
            <p className="text-[#f59e0b] text-xs font-semibold">[ATTORNEY REVIEW REQUIRED — Verify DMCA safe harbor compliance and designated agent registration with U.S. Copyright Office]</p>
          </section>

          {/* 9 */}
          <section>
            <h2>9. Payment Terms</h2>
            <ul>
              <li><strong>Payment processing:</strong> All payments are processed through Stripe. By using Melodio, you agree to Stripe&apos;s terms of service.</li>
              <li><strong>Minimum payout:</strong> Artist royalty payouts require a minimum balance of $25.00 USD. Balances below this threshold are carried forward to the next payout period.</li>
              <li><strong>Payout schedule:</strong> Quarterly payouts processed within 30 days of the end of each quarter.</li>
              <li><strong>Tax reporting:</strong> Melodio will issue IRS Form 1099-MISC to U.S.-based users who earn $600 or more in a calendar year. International users are responsible for their own tax reporting.</li>
              <li><strong>Currency:</strong> All amounts are denominated in USD. International payouts may be subject to currency conversion fees imposed by your bank or payment provider.</li>
            </ul>
            <p className="text-[#f59e0b] text-xs font-semibold">[ATTORNEY REVIEW REQUIRED — Verify 1099 thresholds, international tax treaty obligations, and Stripe terms integration]</p>
          </section>

          {/* 10 */}
          <section>
            <h2>10. Data Privacy</h2>
            <p>
              Melodio is committed to protecting your personal data in compliance with applicable
              privacy laws, including the General Data Protection Regulation (GDPR) and the
              California Consumer Privacy Act (CCPA).
            </p>
            <ul>
              <li><strong>Data collection:</strong> We collect personal information necessary to operate the Service, including name, email, payment information, streaming data, and usage analytics.</li>
              <li><strong>Data use:</strong> Your data is used to provide the Service, process payments, communicate with you, improve our platform, and comply with legal obligations.</li>
              <li><strong>Data sharing:</strong> We share data with third-party service providers (Stripe, SendGrid, DSPs) only as necessary to operate the Service. We do not sell your personal data.</li>
              <li><strong>Right to access:</strong> You may request a copy of all personal data we hold about you.</li>
              <li><strong>Right to deletion:</strong> You may request deletion of your personal data, subject to legal retention requirements.</li>
              <li><strong>Data portability:</strong> You may request your data in a machine-readable format.</li>
            </ul>
            <p>
              For privacy inquiries, contact <strong>privacy@melodio.io</strong>.
            </p>
            <p className="text-[#f59e0b] text-xs font-semibold">[ATTORNEY REVIEW REQUIRED — Full privacy policy should be a separate document. Verify GDPR DPA requirements, CCPA opt-out provisions, and international data transfer mechanisms]</p>
          </section>

          {/* 11 */}
          <section>
            <h2>11. Limitation of Liability</h2>
            <p>
              TO THE MAXIMUM EXTENT PERMITTED BY APPLICABLE LAW, MELODIO AND ITS OFFICERS,
              DIRECTORS, EMPLOYEES, AGENTS, AND AFFILIATES SHALL NOT BE LIABLE FOR ANY INDIRECT,
              INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES, OR ANY LOSS OF PROFITS OR
              REVENUES, WHETHER INCURRED DIRECTLY OR INDIRECTLY, OR ANY LOSS OF DATA, USE, GOODWILL,
              OR OTHER INTANGIBLE LOSSES, RESULTING FROM:
            </p>
            <ul>
              <li>YOUR USE OF OR INABILITY TO USE THE SERVICE;</li>
              <li>ANY UNAUTHORIZED ACCESS TO OR USE OF OUR SERVERS AND/OR ANY PERSONAL INFORMATION STORED THEREIN;</li>
              <li>ANY INTERRUPTION OR CESSATION OF TRANSMISSION TO OR FROM THE SERVICE;</li>
              <li>ANY BUGS, VIRUSES, OR OTHER HARMFUL CODE TRANSMITTED THROUGH THE SERVICE;</li>
              <li>FLUCTUATIONS IN STREAMING REVENUE OR MELODIO POINTS VALUE.</li>
            </ul>
            <p>
              OUR TOTAL LIABILITY SHALL NOT EXCEED THE GREATER OF (A) THE AMOUNTS YOU HAVE PAID TO
              MELODIO IN THE 12 MONTHS PRIOR TO THE CLAIM, OR (B) $100 USD.
            </p>
            <p className="text-[#f59e0b] text-xs font-semibold">[ATTORNEY REVIEW REQUIRED — Verify enforceability of liability cap in all jurisdictions, especially EU/UK]</p>
          </section>

          {/* 12 */}
          <section>
            <h2>12. Dispute Resolution</h2>
            <p>
              Any dispute, controversy, or claim arising out of or relating to these Terms or the
              Service shall be resolved through binding arbitration administered by the American
              Arbitration Association (AAA) under its Commercial Arbitration Rules.
            </p>
            <ul>
              <li>Arbitration shall take place in San Francisco, California.</li>
              <li>The arbitrator&apos;s decision shall be final and binding.</li>
              <li>You agree to waive your right to a jury trial and to participate in class action lawsuits.</li>
              <li>Small claims court actions (under $10,000) may be brought in the courts of San Francisco County, California.</li>
            </ul>
            <p className="text-[#f59e0b] text-xs font-semibold">[ATTORNEY REVIEW REQUIRED — Critical: class action waiver enforceability, arbitration clause validity in EU/UK, AAA fee allocation]</p>
          </section>

          {/* 13 */}
          <section>
            <h2>13. Termination</h2>
            <ul>
              <li><strong>Artist termination:</strong> Artists may terminate their agreement with Melodio at any time by providing written notice to support@melodio.io. Upon termination, a final royalty payout will be processed within 30 days.</li>
              <li><strong>Points obligations:</strong> Termination does not extinguish existing Melodio Points obligations. Point holders will continue to receive royalty distributions until all Points expire per their original terms.</li>
              <li><strong>Content removal:</strong> Upon termination, Melodio will initiate takedown of the artist&apos;s content from all DSPs within 30 business days, subject to DSP processing timelines.</li>
              <li><strong>Melodio termination:</strong> Melodio may terminate your account for material breach of these Terms, with 14 days&apos; written notice and opportunity to cure.</li>
            </ul>
            <p className="text-[#f59e0b] text-xs font-semibold">[ATTORNEY REVIEW REQUIRED — Verify termination provisions, especially regarding ongoing Points obligations post-termination]</p>
          </section>

          {/* 14 */}
          <section>
            <h2>14. Governing Law</h2>
            <p>
              These Terms shall be governed by and construed in accordance with the laws of the
              State of California, United States of America, without regard to its conflict of law
              provisions.
            </p>
            <p className="text-[#f59e0b] text-xs font-semibold">[ATTORNEY REVIEW REQUIRED — Verify choice of law enforceability for international users]</p>
          </section>

          {/* 15 */}
          <section>
            <h2>15. Contact</h2>
            <p>
              For questions about these Terms, contact us at:
            </p>
            <ul>
              <li>Email: <strong>legal@melodio.io</strong></li>
              <li>Website: <strong>melodio.io</strong></li>
            </ul>
          </section>
        </div>

        {/* Footer */}
        <div className="mt-16 pt-8 border-t border-[#2a2a3a] text-center">
          <p className="text-xs text-[#6b7280]">
            This Terms of Service is a draft document and is not legally binding.
            It is subject to legal review and revision before publication.
          </p>
          <Link
            href="/"
            className="inline-block mt-4 text-sm text-[#8b5cf6] hover:text-[#a78bfa] transition-colors"
          >
            ← Back to Home
          </Link>
        </div>
      </div>
    </main>
  );
}
