import React from 'react';
import styles from './homepage.module.css';
import Feature from '../../../src/components/Feature';
import Grid from '../../../src/components/Grid';
import FooterMenu from '../../../src/components/FooterMenu';

const FeatureList = [
  {
    title: 'Redpanda Quickstart',
    image: require('../../../static/img/quickstart.png').default,
    description: (
      <>
        Quickly get started and try out Redpanda.
      </>
    ),
    url: '/docs/get-started/quick-start',
    learnText: true,
  },
  {
    title: 'Use rpk',
    image: require('../../../static/img/RPK-commands.png').default,
    description: (
      <>
        Browse commands or use rpk to interact with the Redpanda platform.
      </>
    ),
    url: '/docs/reference/rpk',
    learnText: true,
  },
  {
    title: 'Deploy Redpanda',
    image: require('../../../static/img/rocket.png').default,
    description: (
      <>
        Configure Redpanda and deploy for production.
      </>
    ),
    url: '/docs/deploy',
    learnText: true,
  },
  {
    title: 'Redpanda Console',
    image: require('../../../static/img/console-icon.png').default,
    description: (
      <>
        Use the Redpanda Console dashboard to administer clusters and get visibility into your data streams.
      </>
    ),
    url: '/docs/manage/console/',
    learnText: true,
  },
  {
    title: 'Tiered Storage',
    image: require('../../../static/img/cloud-first.png').default,
    description: (
      <>
        Save storage costs by offloading log segments to object storage.
      </>
    ),
    url: '/docs/manage/tiered-storage',
    learnText: true,
  },
  {
    title: 'Redpanda on Kubernetes',
    image: require('../../../static/img/redpanda-kubernetes.png').default,
    description: (
      <>
        Get started with Redpanda on the Kubernetes platform.
      </>
    ),
    url: '/docs/deploy/deployment-option/self-hosted/kubernetes/',
    learnText: true,
  },
];

const FooterMenuList = [
  {
    title: 'Get Started',
    icon: {
      url: require('../../../static/img/get-started-icon.png').default,
      size: 'higher',
    },
    items: [
      { text: 'Introduction to Redpanda', url: "/docs/get-started/intro-to-events/" },
      { text: 'How Redpanda Works', url: "/docs/get-started/architecture/" },
      { text: 'Redpanda Licensing', url: "/docs/get-started/licenses/" },
      { text: 'Redpanda Quickstart', url: "/docs/get-started/quick-start/" },
      { text: 'Introduction to rpk', url: "/docs/get-started/rpk-install/" },
    ],
  },
  {
    title: 'Develop',
    icon: {
      url: require('../../../static/img/develop-icon.png').default,
      size: 'wider',
    },
    items: [
      { text: 'Supported Kafka Clients', url: "/docs/develop/kafka-clients/" },
      { text: 'Use Redpanda with Kafka Client Libraries', url: "/docs/develop/code-examples/" },
      { text: 'Use Redpanda with NodeJS', url: "/docs/develop/guide-nodejs/" },
      { text: 'Use Redpanda with HTTP Proxy API', url: "/docs/develop/http-proxy/" },
      { text: 'Produce Data', url: "/docs/develop/produce-data/" },
      { text: 'Consume Data', url: "/docs/develop/consume-data/" },
      { text: 'Transactions', url: "/docs/develop/transactions" },
    ],
  },
  {
    title: 'Deploy',
    icon: {
      url: require('../../../static/img/deploy-icon.png').default,
      size: 'wider',
    },
    items: [
      { text: 'Cloud Deployment', url: "/docs/deploy/deployment-option/cloud/" },
      { text: 'Self-Hosted Deployment', url: "/docs/deploy/deployment-option/self-hosted/" },
      { text: 'Sizing Guidelines', url: "/docs/deploy/deployment-option/self-hosted/manual/sizing/" },
      { text: 'Sizing Use Cases', url: "/docs/deploy/deployment-option/self-hosted/manual/sizing-use-cases/" },
      { text: 'High Availability', url: "/docs/deploy/deployment-option/self-hosted/manual/high-availability/" },
      
    ],
  },
  {
    title: 'Manage',
    icon: {
      url: require('../../../static/img/manage-icon.png').default,
      size: 'default',
    },
    items: [
      { text: 'Redpanda on Kubernetes', url: "/docs/manage/kubernetes/" },
      { text: 'Redpanda Console', url: "/docs/manage/console/" },
      { text: 'Security', url: "/docs/manage/security/" },
      { text: 'Schema Registry', url: "/docs/manage/schema-registry/" },
      { text: 'Monitor Redpanda', url: "/docs/manage/monitoring/" },
      { text: 'Continuous Data Balancing', url: "/docs/manage/cluster-maintenance/continuous-data-balancing/" },
    ],
  },
];

export default function HomepageFeatures() {
  return (
    <section className={styles.features}>
      <Grid gap="2rem" minWidth="300px">
        {FeatureList.map((props, idx) => (
          <Feature key={idx} {...props} />
        ))}
      </Grid>
      <Grid gap="3.85rem" minWidth="175px" title='Highlights'>
        {FooterMenuList.map((props, idx) => (
          <FooterMenu key={idx} {...props} />
        ))}
      </Grid>
    </section >
  );
}