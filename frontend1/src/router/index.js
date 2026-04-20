import { createRouter, createWebHistory } from 'vue-router'

const Home = () => import('@/views/Home.vue')
const DetectChanges = () => import('@/views/mainfun/DetectChanges.vue')
const DetectObjects = () => import('@/views/mainfun/DetectObjects.vue')
const Segmentation = () => import('@/views/mainfun/Segmentation.vue')
const Classification = ()=> import('@/views/mainfun/Classification')
const RestoreImgs = ()=> import('@/views/mainfun/RestoreImgs')
const OnlineMap = () => import('@/views/mainfun/OnlineMap.vue')
const Fa1 = () => import('@/views/mainfun/fa1.vue')
const SmsSender = () => import('@/views/mainfun/SmsSender.vue')
const History = () => import('@/views/history/History.vue')
const NotFound = () => import('@/views/NotFound.vue')
const routes = [
  {
    path: '/',
    redirect: '/home'
  },
  {
    path: '/home',
    name: 'Home',
    component: Home,
    redirect: '/detectchanges',
    children: [
      {
        path: '/detectchanges',
        name: 'Detectchanges',
        component: DetectChanges,

      }, {
        path: '/detectobjects',
        name: 'Detectobjects',
        component: DetectObjects
      },  {
        path: '/segmentation',
        name: 'Segmentation',
        component: Segmentation
      },
      {
        path: '/classification',
        name:'Classification',
        component:Classification
      },
      {
        path:'/restoreimgs',
        name:'Restoreimgs',
        component:RestoreImgs
      },
      {
        path: '/history',
        name: 'history',
        component: History,
      },
      {
        path:'/onlinemap',
        name:'onlinemap',
        component:SmsSender
      },
      {
        path:'/classification2',
        name:'classification2',
        component:OnlineMap
      },
      {
        path:'/onlinemap1',
        name:'onlinemap1',
        component:Fa1
      },
      {
        path:'/history1',
        name:'history1',
        component:History
      }
    ]
  },
  {
    path: "/:pathMatch(.*)*",
    name: 'notfound',
    component: NotFound
  }
]

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes,
})
export default router
